"""
Enhanced Chat Routes - Natural Persona Interactions

Uses the enhanced persona service with:
- Natural empathy assessment (not mechanistic scoring)
- Staged knowledge revelation
- Micro-behavioral adjustments
- Character consistency validation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from src.services.enhanced_persona_service import enhanced_persona_service, PersonaResponse, InteractionContext
from src.dependencies import get_supabase_client
from src.services.short_term_memory_service import short_term_memory
from src.services.analytics_service import analytics
from src.auth import AuthenticatedUser, get_current_user, require_full_access

logger = logging.getLogger(__name__)
router = APIRouter()

class PersonaInfo(BaseModel):
    """Persona information for selection screen"""
    id: str
    name: str
    description: str

class EnhancedChatRequest(BaseModel):
    message: str
    persona_id: str
    session_id: str
    conversation_id: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None
    persona_llm: Optional[str] = "gpt-4o-mini"

class EnhancedChatResponse(BaseModel):
    """Enhanced response with rich interaction context"""
    conversation_id: str
    response: str
    trust_level: float
    
    # Rich interaction context (more natural than MI scores)
    interaction_quality: str  # poor, adequate, good, excellent
    empathy_tone: str  # hostile, neutral, supportive, deeply_empathetic
    user_approach: str  # directive, questioning, reflective, collaborative
    trust_trajectory: str  # declining, stable, building, breakthrough
    
    # Character context
    knowledge_tier_used: str  # defensive, cautious, opening, trusting
    emotional_state: str
    character_notes: str
    
    # Safety and validation
    emotional_safety: bool
    is_safe: bool

class StartConversationRequest(BaseModel):
    """Request to start a new conversation"""
    persona_id: str

class StartConversationResponse(BaseModel):
    """Response when starting a conversation"""
    conversation_id: str
    session_id: str
    persona_name: str
    persona_id: str
    initial_greeting: str

@router.post("/start", response_model=StartConversationResponse)
async def start_enhanced_conversation(
    request: StartConversationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Start a new enhanced conversation with natural empathy assessment

    Accessible by: Both FULL and CONTROL users
    """
    try:
        logger.info(f"User {current_user.email} starting conversation with persona {request.persona_id}")
        supabase = get_supabase_client()
        
        # Get enhanced persona details
        persona_result = supabase.table('enhanced_personas').select('*').eq(
            'persona_id', request.persona_id
        ).maybe_single().execute()
        
        if not persona_result or not persona_result.data:
            raise HTTPException(status_code=404, detail=f"Persona '{request.persona_id}' not found")
        
        persona_data = persona_result.data
        
        # Generate unique IDs - use same ID for both conversation_id and session_id
        conversation_id = str(uuid.uuid4())
        session_id = conversation_id  # Same UUID, no "session_" prefix needed
        
        # Create persona_seed from available data
        persona_seed = f"{persona_data['name']} - {persona_data['description']}"
        
        # Create conversation record
        conv_data = {
            'id': conversation_id,
            'persona_id': request.persona_id,
            'persona_seed': persona_seed,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat()
        }
        
        conv_result = supabase.table('conversations').insert(conv_data).execute()
        
        if not conv_result or not conv_result.data:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        # Get a random greeting from the persona_greetings table
        greeting_result = supabase.table('persona_greetings').select('greeting_text').eq(
            'is_active', True
        ).execute()
        
        if greeting_result.data:
            import random
            random_greeting = random.choice(greeting_result.data)['greeting_text']
        else:
            # Fallback greeting if no greetings in database
            random_greeting = "Hi there! It's good to connect with you today. How are things going?"
        
        # Start analytics tracking
        analytics.start_session(session_id=session_id, persona_id=request.persona_id)
        
        logger.info(f"✅ Started enhanced conversation: session={session_id}, persona={request.persona_id}")
        
        return StartConversationResponse(
            conversation_id=conversation_id,
            session_id=session_id,
            persona_name=persona_data['name'],
            persona_id=request.persona_id,
            initial_greeting=random_greeting
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting enhanced conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send", response_model=EnhancedChatResponse)
async def send_enhanced_message(
    request: EnhancedChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Send message using enhanced persona system with natural empathy assessment

    Accessible by: Both FULL and CONTROL users
    """
    try:
        supabase = get_supabase_client()
        
        # Use session_id as conversation_id (they're the same UUID)
        conversation_id = request.session_id
        
        # Validate conversation exists
        conversation_exists = supabase.table('conversations').select('persona_id').eq('id', conversation_id).maybe_single().execute()
        if not conversation_exists.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        persona_id = conversation_exists.data.get('persona_id', request.persona_id)
        
        # Get current turn number
        turn_result = supabase.table('conversation_transcripts') \
            .select('turn_number') \
            .eq('conversation_id', conversation_id) \
            .order('turn_number', desc=True) \
            .limit(1) \
            .execute()
        
        turn_number = (turn_result.data[0]['turn_number'] + 1) if turn_result.data else 1
        
        # Store user message in transcript
        supabase.table('conversation_transcripts').insert({
            'conversation_id': conversation_id,
            'turn_number': turn_number,
            'role': 'user',
            'message': request.message,
            'timestamp': datetime.utcnow().isoformat()
        }).execute()
        
        # Add user message to short-term memory
        short_term_memory.add_message(
            session_id=conversation_id,
            role='user',
            content=request.message,
            turn_number=turn_number
        )
        
        # Track user message in analytics
        analytics.add_message(
            session_id=conversation_id,
            role='user'
        )
        
        # Get recent conversation history from short-term memory (fast)
        conversation_history = short_term_memory.get_recent_messages(
            session_id=conversation_id,
            limit=12  # Keep last 12 messages for context
        )
        
        logger.info(f"📨 Processing enhanced turn {turn_number} for persona={persona_id}, conv={conversation_id}")
        
        # Call enhanced persona service with natural empathy assessment
        result: PersonaResponse = await enhanced_persona_service.process_conversation(
            user_message=request.message,
            persona_id=persona_id,
            session_id=conversation_id,
            conversation_history=conversation_history,
            persona_llm=request.persona_llm or "gpt-4o-mini"
        )
        
        # Store persona response in transcript
        supabase.table('conversation_transcripts').insert({
            'conversation_id': conversation_id,
            'turn_number': turn_number,
            'role': 'persona',
            'message': result.response,
            'timestamp': datetime.utcnow().isoformat()
        }).execute()
        
        # Add persona response to short-term memory
        short_term_memory.add_message(
            session_id=conversation_id,
            role='persona',
            content=result.response,
            turn_number=turn_number
        )
        
        # Track persona response with analytics
        analytics.add_message(
            session_id=conversation_id,
            role='persona',
            trust_level=result.trust_level,
            interaction_quality=result.interaction_context.interaction_quality,
            knowledge_tier=result.knowledge_tier_used
        )
        
        # Log enhanced interaction details
        logger.info(f"🎭 Enhanced interaction complete:")
        logger.info(f"   Quality: {result.interaction_context.interaction_quality}")
        logger.info(f"   Empathy: {result.interaction_context.empathy_tone}")
        logger.info(f"   Approach: {result.interaction_context.user_approach}")
        logger.info(f"   Trust: {result.trust_level:.2f} ({result.interaction_context.trust_trajectory})")
        logger.info(f"   Tier: {result.knowledge_tier_used}")
        
        # Return enhanced response with rich context
        return EnhancedChatResponse(
            conversation_id=conversation_id,
            response=result.response,
            trust_level=result.trust_level,
            
            # Rich interaction context
            interaction_quality=result.interaction_context.interaction_quality,
            empathy_tone=result.interaction_context.empathy_tone,
            user_approach=result.interaction_context.user_approach,
            trust_trajectory=result.interaction_context.trust_trajectory,
            
            # Character context
            knowledge_tier_used=result.knowledge_tier_used,
            emotional_state=result.emotional_state,
            character_notes=result.character_notes,
            
            # Safety
            emotional_safety=result.interaction_context.emotional_safety,
            is_safe=result.interaction_context.emotional_safety
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Enhanced chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personas", response_model=List[PersonaInfo])
async def get_enhanced_personas():
    """Get all available personas for enhanced chat"""
    try:
        supabase = get_supabase_client()
        result = supabase.table('enhanced_personas').select('persona_id, name, description').execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="No personas found in database. Run migrations to create personas."
            )
        
        personas = []
        for persona_data in result.data:
            personas.append(PersonaInfo(
                id=persona_data['persona_id'],
                name=persona_data['name'],
                description=persona_data['description']
            ))
        
        return personas
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching personas for enhanced chat: {e}")
        raise HTTPException(status_code=500, detail="Database error loading personas")

@router.get("/conversations/{conversation_id}")
async def get_enhanced_conversation(conversation_id: str):
    """
    Get full enhanced conversation with rich interaction context
    """
    try:
        supabase = get_supabase_client()
        
        # Get conversation metadata
        conv_result = supabase.table('conversations').select('*').eq(
            'id', conversation_id
        ).maybe_single().execute()
        
        if not conv_result.data:
            raise HTTPException(status_code=404, detail=f"Conversation '{conversation_id}' not found")

        # Get persona details
        persona_id = conv_result.data.get('persona_id')
        persona_data = None
        if persona_id:
            persona_result = supabase.table('enhanced_personas').select('persona_id, name, description').eq(
                'persona_id', persona_id
            ).maybe_single().execute()
            if persona_result.data:
                persona_data = persona_result.data

        # Try to get recent messages from short-term memory first (faster)
        recent_messages = short_term_memory.get_recent_messages(conversation_id)
        
        if recent_messages:
            # Use cached messages and supplement with older ones from database if needed
            messages = []
            for msg in recent_messages:
                messages.append({
                    'role': msg['role'],
                    'message': msg['content'],  # Convert from 'content' to 'message'
                    'turn_number': msg['turn_number'],
                    'timestamp': msg['timestamp']
                })
            
            # If we have fewer than 20 messages in cache, get older ones from database
            if len(messages) < 20:
                transcript_result = supabase.table('conversation_transcripts').select('*').eq(
                    'conversation_id', conversation_id
                ).order('turn_number').order('timestamp').execute()
                
                # Add older messages not in short-term memory
                cached_turn_numbers = {msg['turn_number'] for msg in recent_messages}
                for msg in transcript_result.data:
                    if msg['turn_number'] not in cached_turn_numbers:
                        messages.insert(0, {  # Insert at beginning for chronological order
                            'role': msg['role'],
                            'message': msg['message'],
                            'turn_number': msg['turn_number'],
                            'timestamp': msg['timestamp']
                        })
        else:
            # Fallback to database if no short-term memory
            transcript_result = supabase.table('conversation_transcripts').select('*').eq(
                'conversation_id', conversation_id
            ).order('turn_number').order('timestamp').execute()
            
            messages = []
            for msg in transcript_result.data:
                messages.append({
                    'role': msg['role'],
                    'message': msg['message'],
                    'turn_number': msg['turn_number'],
                    'timestamp': msg['timestamp']
                })
        
        # Get conversation memories for context
        memories_result = supabase.table('conversation_memories').select('*').eq(
            'session_id', conversation_id
        ).order('importance_score', desc=True).limit(10).execute()
        
        return {
            'conversation_id': conversation_id,  # Frontend expects snake_case
            'persona': persona_data,  # Include full persona object with name
            'messages': messages,
            'message_count': len(messages),
            'memories': memories_result.data if memories_result.data else [],
            'created_at': conv_result.data.get('created_at'),
            'enhanced_features': True  # Flag to indicate this uses enhanced service
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching enhanced conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/interaction-analysis/{conversation_id}")
async def get_interaction_analysis(conversation_id: str):
    """
    Debug endpoint: Get detailed analysis of interactions in conversation
    Shows natural empathy assessment vs mechanistic scoring
    """
    try:
        supabase = get_supabase_client()
        
        # Get conversation memories with their contextual assessments
        memories_result = supabase.table('conversation_memories').select('*').eq(
            'session_id', conversation_id
        ).order('created_at', desc=False).execute()
        
        # Get conversation transcript
        transcript_result = supabase.table('conversation_transcripts').select('*').eq(
            'conversation_id', conversation_id
        ).order('turn_number').execute()
        
        # Analyze interaction patterns
        interaction_analysis = []
        user_messages = [msg for msg in transcript_result.data if msg['role'] == 'user']
        
        for i, user_msg in enumerate(user_messages):
            # Find corresponding persona response
            persona_responses = [msg for msg in transcript_result.data 
                               if msg['role'] == 'persona' and msg['turn_number'] == user_msg['turn_number']]
            persona_response = persona_responses[0] if persona_responses else None
            
            # Find corresponding memory
            corresponding_memories = [mem for mem in memories_result.data 
                                    if f"User said: '{user_msg['message'][:50]}" in mem.get('key_insights', '')]
            memory = corresponding_memories[0] if corresponding_memories else None
            
            interaction_analysis.append({
                'turn_number': user_msg['turn_number'],
                'user_message': user_msg['message'],
                'persona_response': persona_response['message'] if persona_response else None,
                'memory_formed': memory['key_insights'] if memory else None,
                'memory_importance': memory['importance_score'] if memory else None,
                'timestamp': user_msg['timestamp']
            })
        
        return {
            'conversation_id': conversation_id,
            'total_turns': len(user_messages),
            'interaction_analysis': interaction_analysis,
            'memories_formed': len(memories_result.data),
            'analysis_type': 'natural_empathy_assessment'
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting interaction analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/trust-progression/{conversation_id}")
async def get_trust_progression(conversation_id: str):
    """
    Debug endpoint: Show how trust progressed throughout conversation
    """
    try:
        supabase = get_supabase_client()
        
        # Get memories in chronological order
        memories_result = supabase.table('conversation_memories').select('*').eq(
            'session_id', conversation_id
        ).order('created_at', desc=False).execute()
        
        # Analyze trust progression from memories
        trust_progression = []
        
        for memory in memories_result.data:
            memory_text = memory.get('key_insights', '')
            importance = memory.get('importance_score', 0)
            
            # Extract trust indicators from memory
            trust_indicators = []
            if 'deeply understood' in memory_text.lower():
                trust_indicators.append('breakthrough_empathy')
            if 'trust' in memory_text.lower() and 'growing' in memory_text.lower():
                trust_indicators.append('building_trust')
            if 'defensive' in memory_text.lower() or 'guarded' in memory_text.lower():
                trust_indicators.append('defensive_response')
            if 'hostile' in memory_text.lower() or 'unsafe' in memory_text.lower():
                trust_indicators.append('trust_decline')
            
            trust_progression.append({
                'memory_text': memory_text,
                'importance': importance,
                'trust_indicators': trust_indicators,
                'timestamp': memory.get('created_at')
            })
        
        return {
            'conversation_id': conversation_id,
            'trust_progression': trust_progression,
            'total_memories': len(memories_result.data),
            'system_type': 'enhanced_natural_assessment'
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting trust progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/character-knowledge/{persona_id}")
async def get_character_knowledge_tiers(persona_id: str):
    """
    Debug endpoint: Show all knowledge tiers for a character
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table('character_knowledge_tiers').select('*').eq(
            'persona_id', persona_id
        ).order('trust_threshold', desc=False).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404, 
                detail=f"No knowledge tiers found for persona '{persona_id}'"
            )
        
        return {
            'persona_id': persona_id,
            'knowledge_tiers': [
                {
                    'tier_name': tier['tier_name'],
                    'trust_threshold': tier['trust_threshold'],
                    'knowledge_count': len(tier.get('knowledge_json', {})),
                    'knowledge_topics': list(tier.get('knowledge_json', {}).keys()),
                    'full_knowledge': tier.get('knowledge_json', {})
                }
                for tier in result.data
            ],
            'total_tiers': len(result.data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching character knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/short-term-memory")
async def get_short_term_memory_stats():
    """
    Debug endpoint: Get short-term memory usage statistics
    """
    try:
        usage_stats = short_term_memory.get_memory_usage()
        active_sessions = short_term_memory.get_all_sessions()
        
        session_details = []
        for session_id in active_sessions[:10]:  # Show details for first 10 sessions
            stats = short_term_memory.get_session_stats(session_id)
            session_details.append({
                'session_id': session_id[:8] + '...',  # Truncate for privacy
                **stats
            })
        
        return {
            'memory_usage': usage_stats,
            'active_sessions_count': len(active_sessions),
            'session_details': session_details,
            'system_info': {
                'max_messages_per_session': short_term_memory.max_messages,
                'cleanup_interval_hours': short_term_memory._cleanup_interval / 3600
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting short-term memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """
    Analytics dashboard with overall statistics
    """
    try:
        # Get overall stats for last 7 days
        overall_stats = analytics.get_overall_stats(days=7)
        
        # Get today's stats
        today_stats = analytics.get_daily_stats()
        
        # Get trust analysis
        trust_analysis = analytics.get_trust_analysis(days=7)
        
        return {
            'overall_stats': overall_stats,
            'today_stats': today_stats,
            'trust_analysis': trust_analysis,
            'generated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/session/{session_id}")
async def get_session_analytics(session_id: str):
    """
    Get detailed analytics for a specific session
    """
    try:
        session_stats = analytics.get_session_stats(session_id)
        
        if not session_stats:
            raise HTTPException(status_code=404, detail="Session not found in analytics")
        
        # Also get short-term memory stats for comparison
        memory_stats = short_term_memory.get_session_stats(session_id)
        
        return {
            'analytics': session_stats,
            'memory_stats': memory_stats,
            'session_id': session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting session analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/persona/{persona_id}")
async def get_persona_analytics(persona_id: str, days: int = 7):
    """
    Get analytics for a specific persona
    """
    try:
        # Get trust analysis for this persona
        trust_analysis = analytics.get_trust_analysis(persona_id=persona_id, days=days)
        
        # Get overall stats filtered by this persona would require additional method
        # For now, return trust analysis
        return {
            'persona_id': persona_id,
            'period_days': days,
            'trust_analysis': trust_analysis,
            'generated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting persona analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        logger.error(f"❌ Error getting character knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))