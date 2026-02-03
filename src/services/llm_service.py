"""
Service for LLM interactions with multiple providers
Includes circuit breaker pattern for resilience
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
import openai
from openai import AsyncOpenAI
import anthropic
import numpy as np
from difflib import SequenceMatcher
import time
from src.services.metrics_service import metrics
from src.services.circuit_breaker import (
    circuit_registry,
    CircuitBreakerOpenError,
    get_openai_breaker,
    get_anthropic_breaker
)

from src.config.settings import get_settings
from src.models.schemas import Message
from src.exceptions import LLMServiceError
from src.core.constants import APIConstants

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM interactions with circuit breaker protection"""
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.anthropic_client = None
        if self.settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY)
        
        self.default_model = self.settings.DEFAULT_MODEL
        self.max_retries = APIConstants.MAX_RETRIES
        self.retry_delay = APIConstants.RETRY_DELAY_BASE
        self.timeout_seconds = 30  # 30 second timeout for LLM calls
        
        # Anti-repetition mechanisms - track last responses
        self.recent_responses = {}  # session_id -> list of recent responses
        self.max_recent_responses = 10  # Track last 10 responses
        self.similarity_threshold = 0.7  # Reject responses with >70% similarity
        
        # Initialize circuit breakers
        self._circuit_initialized = False
    
    async def _initialize_circuits(self):
        """Initialize circuit breakers on first use"""
        if not self._circuit_initialized:
            await circuit_registry.initialize()
            self._circuit_initialized = True
        
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        conversation_history: Optional[List[Message]] = None,
        session_id: Optional[str] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate response using LLM API"""
        
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.settings.TEMPERATURE
        
        # Set anti-repetition penalty defaults
        frequency_penalty = frequency_penalty if frequency_penalty is not None else 0.7
        presence_penalty = presence_penalty if presence_penalty is not None else 0.6
        
        logger.debug(f"LLM Service - Model: {model}, Temperature: {temperature}, Max Tokens: {max_tokens}")
        logger.debug(f"Anti-repetition - Frequency penalty: {frequency_penalty}, Presence penalty: {presence_penalty}")
        # Ensure temperature is within valid range (0.0 to 2.0 for OpenAI)
        if temperature > 2.0:
            logger.warning(f"Temperature {temperature} is too high, clamping to 2.0")
            temperature = 2.0
        elif temperature < 0.0:
            logger.warning(f"Temperature {temperature} is too low, clamping to 0.0")
            temperature = 0.0
        max_tokens = max_tokens or self.settings.MAX_TOKENS
        
        # Build messages list with enhanced conversation history for ALL LLMs
        messages = []
        
        # Add system prompt with stronger format for ALL LLMs (not just gpt-4o-mini)
        if system_prompt:
            # Extract persona name for consistent identity reinforcement across ALL LLMs
            # Get persona name from system prompt - NO hardcoded defaults
            persona_name = "Unknown"  # Will be overridden from Supabase system_prompt
            if "You are " in system_prompt:
                try:
                    name_start = system_prompt.find("You are ") + 8
                    name_end = system_prompt.find(",", name_start)
                    if name_end == -1:
                        name_end = system_prompt.find(".", name_start)
                    if name_end > name_start:
                        persona_name = system_prompt[name_start:name_end].strip()
                except:
                    pass
            
            # Use system prompt EXACTLY as provided from Supabase - no modifications
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history with consistent limits across ALL LLMs
        if conversation_history:
            # Limit to last 16 messages (8 exchanges) for consistent rich context across ALL LLMs
            for message in conversation_history[-16:]:  # Increased from -10
                messages.append({
                    "role": message.role.value,
                    "content": message.content
                })

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        # Debug: Log what we're sending to LLM
        logger.info(f"Sending to LLM - Model: {model}, Messages count: {len(messages)}, System prompt present: {bool(system_prompt)}")
        if system_prompt:
            logger.info(f"System prompt length: {len(system_prompt)} chars")

        # Anti-repetition retry loop
        max_attempts = 3
        for attempt in range(max_attempts):
            # Determine which API to use based on model name
            if model.startswith("claude"):
                response = await self._generate_anthropic_response(
                    messages, model, temperature, max_tokens, stop_sequences,
                    frequency_penalty, presence_penalty
                )
            elif model.startswith("gemini"):
                response = await self._generate_gemini_response(
                    messages, model, temperature, max_tokens, stop_sequences,
                    frequency_penalty, presence_penalty
                )
            else:
                response = await self._generate_openai_response(
                    messages, model, temperature, max_tokens, stop_sequences,
                    frequency_penalty, presence_penalty, response_format
                )
            
            # Check for repetition if session_id provided
            if session_id and self._is_response_repetitive(response, session_id):
                logger.info(f"Attempt {attempt + 1}: Response too repetitive, retrying...")
                if attempt < max_attempts - 1:
                    # Increase penalties for retry
                    frequency_penalty = min(1.0, frequency_penalty + 0.1)
                    presence_penalty = min(1.0, presence_penalty + 0.1)
                    continue
                else:
                    logger.warning("Max anti-repetition attempts reached, using last response")
            
            # Response is acceptable, add to history and return
            if session_id:
                self._add_response_to_history(response, session_id)
            
            return response
    
    async def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stop_sequences: Optional[List[str]] = None,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate response using OpenAI API with circuit breaker protection"""
        
        # Initialize circuits on first use
        await self._initialize_circuits()
        
        # Check circuit breaker
        breaker = await get_openai_breaker()
        if not await breaker.can_execute():
            error_msg = "OpenAI circuit breaker is OPEN - service temporarily unavailable"
            logger.error(error_msg)
            raise LLMServiceError(error_msg, "openai")

        for attempt in range(self.max_retries):
            try:
                async with asyncio.timeout(self.timeout_seconds):
                    # Check if this is a GPT-5 reasoning model (NOT gpt-5-chat-latest)
                    if model.lower() in ["gpt-5", "gpt-5-flash"] or (model.lower().startswith("gpt-5") and "chat" not in model.lower()):
                        return await self._generate_gpt5_response(messages, model, max_tokens)

                    # Debug: Log the exact messages being sent to OpenAI
                    logger.info(f"OpenAI API Request - Model: {model}")
                    for i, msg in enumerate(messages):
                        logger.info(f"Message {i}: Role={msg['role']}, Content={msg['content'][:100]}...")

                    # Prepare request params for GPT-4 and earlier models
                    request_params = {
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "frequency_penalty": frequency_penalty,
                        "presence_penalty": presence_penalty
                    }

                    # Enforce JSON object output if requested (for supported models)
                    if response_format:
                        request_params["response_format"] = response_format

                    # Only add temperature if not using gpt-5 models (which require default temperature=1)
                    if not model.lower().startswith("gpt-5"):
                        request_params["temperature"] = temperature

                    # Only add stop sequences if provided
                    if stop_sequences:
                        request_params["stop"] = stop_sequences

                    t0 = time.time()
                    response = await self.openai_client.chat.completions.create(**request_params)
                    latency_ms = (time.time() - t0) * 1000.0
                    try:
                        metrics.record_llm_call("openai", model, True, latency_ms)
                    except Exception:
                        pass
                    
                    # Record success for circuit breaker
                    await breaker.record_success()

                    return response.choices[0].message.content.strip()

            except asyncio.TimeoutError:
                error_msg = f"OpenAI API call timed out after {self.timeout_seconds} seconds"
                logger.error(error_msg)
                # Record failure for circuit breaker
                await breaker.record_failure()
                raise LLMServiceError(error_msg, "openai")
                
            except Exception as e:
                try:
                    # best-effort latency if t0 defined
                    latency_ms = (time.time() - t0) * 1000.0 if 't0' in locals() else 0.0
                    metrics.record_llm_call("openai", model, False, latency_ms)
                except Exception:
                    pass
                logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")
                # Record failure for circuit breaker
                await breaker.record_failure(e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise LLMServiceError(str(e), "openai")

    async def _generate_gpt5_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int
    ) -> str:
        """Generate response using OpenAI GPT-5 responses API"""

        for attempt in range(self.max_retries):
            try:
                async with asyncio.timeout(self.timeout_seconds):
                    # Convert messages to GPT-5 format
                    # Combine system prompt and user message into input
                    system_content = ""
                    user_content = ""

                    for message in messages:
                        if message["role"] == "system":
                            system_content = message["content"]
                        elif message["role"] == "user":
                            user_content = message["content"]

                    # Combine system and user content
                    input_text = user_content
                    if system_content:
                        input_text = f"{system_content}\n\n{user_content}"

                    # Use GPT-5 responses API (no temperature parameter)
                    t0 = time.time()
                    response = await self.openai_client.responses.create(
                        model=model,
                        input=input_text,
                        reasoning={"effort": "low"},
                        text={"verbosity": "low"}
                    )
                    latency_ms = (time.time() - t0) * 1000.0
                    try:
                        metrics.record_llm_call("openai", model, True, latency_ms)
                    except Exception:
                        pass

                    return response.output_text.strip()

            except asyncio.TimeoutError:
                error_msg = f"GPT-5 API call timed out after {self.timeout_seconds} seconds"
                logger.error(error_msg)
                raise LLMServiceError(error_msg, "openai")

            except Exception as e:
                try:
                    latency_ms = (time.time() - t0) * 1000.0 if 't0' in locals() else 0.0
                    metrics.record_llm_call("openai", model, False, latency_ms)
                except Exception:
                    pass
                logger.warning(f"GPT-5 API attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise LLMServiceError(str(e), "openai")

    async def _generate_anthropic_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stop_sequences: Optional[List[str]] = None,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0
    ) -> str:
        """Generate response using Anthropic API with circuit breaker protection"""
        
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        # Initialize circuits on first use
        await self._initialize_circuits()
        
        # Check circuit breaker
        breaker = await get_anthropic_breaker()
        if not await breaker.can_execute():
            error_msg = "Anthropic circuit breaker is OPEN - service temporarily unavailable"
            logger.error(error_msg)
            raise LLMServiceError(error_msg, "anthropic")
        
        # Convert messages format for Anthropic
        system = None
        anthropic_messages = []
        
        for message in messages:
            if message["role"] == "system":
                system = message["content"]
            else:
                anthropic_messages.append({
                    "role": message["role"],
                    "content": message["content"]
                })
        
        for attempt in range(self.max_retries):
            try:
                async with asyncio.timeout(self.timeout_seconds):
                    t0 = time.time()
                    response = await self.anthropic_client.messages.create(
                        model=model,
                        messages=anthropic_messages,
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stop_sequences=stop_sequences
                    )
                    latency_ms = (time.time() - t0) * 1000.0
                    try:
                        metrics.record_llm_call("anthropic", model, True, latency_ms)
                    except Exception:
                        pass
                    
                    # Record success for circuit breaker
                    await breaker.record_success()
                    
                    return response.content[0].text.strip()
            
            except asyncio.TimeoutError:
                error_msg = f"Anthropic API call timed out after {self.timeout_seconds} seconds"
                logger.error(error_msg)
                # Record failure for circuit breaker
                await breaker.record_failure()
                raise LLMServiceError(error_msg, "anthropic")
                
            except Exception as e:
                try:
                    latency_ms = (time.time() - t0) * 1000.0 if 't0' in locals() else 0.0
                    metrics.record_llm_call("anthropic", model, False, latency_ms)
                except Exception:
                    pass
                logger.warning(f"Anthropic API attempt {attempt + 1} failed: {e}")
                # Record failure for circuit breaker
                await breaker.record_failure(e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise LLMServiceError(str(e), "anthropic")

    async def _generate_gemini_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stop_sequences: Optional[List[str]] = None,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0
    ) -> str:
        """Generate response using Google Gemini API - TEMPORARY: old SDK with 2.5-flash only"""
        if not self.settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured, falling back to OpenAI")
            return await self._generate_openai_response(
                messages, "gpt-4o-mini", temperature, max_tokens, stop_sequences
            )
        
        try:
            # TEMPORARY: Use old SDK until new one is deployed
            import google.generativeai as genai
            
            genai.configure(api_key=self.settings.GEMINI_API_KEY)
            
            # ENFORCE: Only gemini-2.5-flash per user preference
            model_mapping = {
                "gemini": "gemini-2.5-flash",
                "gemini-2.5-flash": "gemini-2.5-flash", 
                # NO 1.5 Flash allowed
            }
            
            gemini_model_name = model_mapping.get(model, "gemini-2.5-flash")
            logger.info(f"Using Gemini model: {gemini_model_name} (enforced: no 1.5 Flash)")
            
            # Try new model first, fallback if not available
            try:
                gemini_model = genai.GenerativeModel(gemini_model_name)
            except Exception as e:
                logger.warning(f"gemini-2.5-flash not available ({e}), falling back to OpenAI")
                return await self._generate_openai_response(
                    messages, "gpt-4o-mini", temperature, max_tokens, stop_sequences
                )
            
            # Enhanced prompt structure for consistent context retention across ALL LLMs
            combined_content = ""
            persona_name = "Assistant"  # Default
            persona_instructions = ""
            conversation_context = ""
            
            for message in messages:
                if message["role"] == "system":
                    persona_instructions = message['content']
                    # Extract persona name for better identity retention (consistent with other LLMs)
                    if "You are " in persona_instructions:
                        try:
                            name_start = persona_instructions.find("You are ") + 8
                            name_end = persona_instructions.find(",", name_start)
                            if name_end == -1:
                                name_end = persona_instructions.find(".", name_start)
                            if name_end > name_start:
                                persona_name = persona_instructions[name_start:name_end].strip()
                        except:
                            pass
                elif message["role"] == "user":
                    conversation_context += f"User: {message['content']}\n"
                elif message["role"] == "assistant":
                    conversation_context += f"{persona_name}: {message['content']}\n"
            
            # Build enhanced prompt for consistent context retention across ALL LLMs
            combined_content = f"""IDENTITY: {persona_instructions}

IMPORTANT: You are {persona_name}. Stay in character throughout this conversation. Do not introduce yourself again unless specifically asked.

CONVERSATION HISTORY:
{conversation_context}

Respond as {persona_name} based on your established identity and the conversation context above."""
            
            # Add recent user message if provided separately
            if messages and messages[-1]["role"] == "user":
                combined_content += f"\n\nUser: {messages[-1]['content']}\n{persona_name}:"
            
            # Use old API temporarily
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                stop_sequences=stop_sequences
            )
            
            t0 = time.time()
            response = await gemini_model.generate_content_async(
                combined_content,
                generation_config=generation_config
            )
            latency_ms = (time.time() - t0) * 1000.0
            
            try:
                metrics.record_llm_call("gemini", gemini_model_name, True, latency_ms)
            except Exception:
                pass
            
            logger.info(f"Gemini API call successful - Model: {gemini_model_name}")
            return response.text.strip()
            
        except Exception as e:
            try:
                latency_ms = (time.time() - t0) * 1000.0 if 't0' in locals() else 0.0
                metrics.record_llm_call("gemini", model, False, latency_ms)
            except Exception:
                pass
            logger.error(f"Gemini 2.5 Flash API error: {e}")
            # Do NOT fallback to 1.5 Flash per user preference - fallback to OpenAI instead
            logger.warning("Gemini 2.5 Flash failed, falling back to OpenAI (user preference: no 1.5 Flash)")
            return await self._generate_openai_response(
                messages, "gpt-4o-mini", temperature, max_tokens, stop_sequences
            )
    
    async def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """Generate text embedding"""
        model = model or self.settings.EMBEDDING_MODEL
        
        try:
            response = await self.openai_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def estimate_token_count(self, text: str) -> int:
        """Estimate the number of tokens in the given text"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text responses"""
        # Use sequence matcher for quick similarity check
        return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()
    
    def _is_response_repetitive(self, response: str, session_id: str) -> bool:
        """Check if response is too similar to recent responses"""
        if session_id not in self.recent_responses:
            return False
        
        for recent_response in self.recent_responses[session_id]:
            similarity = self._calculate_similarity(response, recent_response)
            if similarity > self.similarity_threshold:
                logger.warning(f"Rejecting repetitive response (similarity: {similarity:.2f})")
                return True
        
        return False
    
    def _add_response_to_history(self, response: str, session_id: str):
        """Add response to history for anti-repetition tracking"""
        if session_id not in self.recent_responses:
            self.recent_responses[session_id] = []
        
        # Add new response and keep only last N responses
        self.recent_responses[session_id].append(response)
        if len(self.recent_responses[session_id]) > self.max_recent_responses:
            self.recent_responses[session_id].pop(0)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_case: Optional[str] = None,
        **kwargs
    ) -> 'LLMResponse':
        """Simple completion interface for persona responses"""
        response_text = await self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            session_id=use_case
        )
        return LLMResponse(content=response_text)

    async def structured_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_case: Optional[str] = None,
        response_format: Optional[str] = None,
        **kwargs
    ) -> 'LLMResponse':
        """Structured completion interface for analysis responses"""
        response_format_dict = {"type": "json_object"} if response_format == "json" else None
        response_text = await self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            session_id=use_case,
            response_format=response_format_dict
        )
        return LLMResponse(content=response_text)


class LLMResponse:
    """Simple response wrapper for LLM completions"""
    def __init__(self, content: str):
        self.content = content


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the singleton LLMService"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
