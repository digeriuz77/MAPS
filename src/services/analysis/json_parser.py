"""
Enhanced JSON parsing utilities for robust MITI analysis response handling
"""
import json
import re
import logging
from typing import List, Dict, Any, Optional
from .types import (
    AnnotatedTurn, ParsedTurn, MitiCode, SpeakerRole, 
    ALL_MITI_CODES, PRACTITIONER_CODES, CLIENT_CODES
)

logger = logging.getLogger(__name__)

class JsonParsingError(Exception):
    """Custom exception for JSON parsing failures"""
    pass

def clean_and_validate_json_response(
    raw_response: str, 
    batch_turns: List[ParsedTurn]
) -> List[Dict[str, Any]]:
    """
    Clean and validate JSON response from AI with comprehensive error recovery.
    
    Args:
        raw_response: Raw text response from AI model
        batch_turns: Original parsed turns for fallback creation
        
    Returns:
        List of validated turn objects
    """
    logger.debug(f"Processing JSON response with length: {len(raw_response)}")
    
    try:
        # Step 1: Initial cleaning
        cleaned = _initial_clean_response(raw_response)
        
        # Step 2: Extract JSON array bounds
        json_content = _extract_json_array(cleaned)
        
        # Step 3: Fix common JSON issues
        json_content = _fix_common_json_issues(json_content)
        
        # Step 4: Attempt parsing
        parsed = _attempt_json_parsing(json_content)
        
        # Step 5: Validate and fix turn objects
        validated = _validate_and_fix_turn_objects(parsed, batch_turns)
        
        logger.info(f"Successfully processed {len(validated)} turns from AI response")
        return validated
        
    except Exception as e:
        logger.error(f"JSON parsing failed completely: {e}")
        # Return fallback turns for all expected turns
        return _create_fallback_turns(batch_turns)

def _initial_clean_response(raw_response: str) -> str:
    """Clean markdown formatting and basic whitespace"""
    cleaned = raw_response.strip()
    
    # Remove markdown code fences
    fence_pattern = r'^```(?:\w+)?\s*\n?(.*?)\n?\s*```$'
    match = re.match(fence_pattern, cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    
    # Normalize line endings
    cleaned = re.sub(r'\r\n|\r', '\n', cleaned)
    cleaned = re.sub(r'^\s*[\r\n]+', '', cleaned, flags=re.MULTILINE)
    
    return cleaned

def _extract_json_array(cleaned: str) -> str:
    """Extract JSON array content from cleaned response"""
    array_start = cleaned.find('[')
    array_end = cleaned.rfind(']')
    
    if array_start == -1 or array_end == -1 or array_end <= array_start:
        raise JsonParsingError("No valid JSON array bounds found")
    
    return cleaned[array_start:array_end + 1]

def _fix_common_json_issues(json_content: str) -> str:
    """Apply common JSON formatting fixes"""
    fixed = json_content
    
    # Fix missing commas between objects
    fixed = re.sub(r'}\s*{', '}, {', fixed)
    
    # Fix missing commas after property values
    fixed = re.sub(
        r'("[\w]+"\s*:\s*(?:"[^"]*"|[\d.]+|true|false|null|\[[^\]]*\]|\{[^}]*\}))\s*(?=["}])',
        r'\1,',
        fixed
    )
    
    # Fix double commas
    fixed = re.sub(r',\s*,+', ',', fixed)
    
    # Fix trailing commas
    fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
    
    return fixed

def _attempt_json_parsing(json_content: str) -> List[Dict]:
    """Attempt JSON parsing with progressive truncation fallback"""
    # First attempt: direct parsing
    try:
        parsed = json.loads(json_content)
        if isinstance(parsed, list):
            return parsed
        else:
            raise JsonParsingError("Response is not a JSON array")
    except json.JSONDecodeError:
        pass
    
    # Second attempt: balance brackets and retry
    try:
        balanced = _balance_json_array(json_content)
        parsed = json.loads(balanced)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Third attempt: progressive truncation
    return _attempt_progressive_truncation(json_content)

def _balance_json_array(json_string: str) -> str:
    """Balance JSON brackets and braces"""
    balanced = json_string.strip()
    open_brackets = open_braces = 0
    
    # Count unbalanced brackets/braces
    for char in balanced:
        if char == '[':
            open_brackets += 1
        elif char == ']':
            open_brackets -= 1
        elif char == '{':
            open_braces += 1
        elif char == '}':
            open_braces -= 1
    
    # Add missing closing brackets/braces
    while open_braces > 0:
        balanced += '}'
        open_braces -= 1
    while open_brackets > 0:
        balanced += ']'
        open_brackets -= 1
    
    # Ensure array wrapper
    if not balanced.startswith('['):
        balanced = '[' + balanced
    if not balanced.endswith(']'):
        balanced = balanced + ']'
    
    return balanced

def _attempt_progressive_truncation(json_content: str) -> List[Dict]:
    """Attempt parsing by progressively truncating content"""
    lines = json_content.split('\n')
    min_lines = max(1, len(lines) // 2)
    
    for i in range(len(lines), min_lines - 1, -1):
        try:
            truncated = '\n'.join(lines[:i]).strip()
            
            # Ensure proper array format
            if not truncated.startswith('['):
                truncated = '[' + truncated
            if not truncated.endswith(']'):
                truncated = truncated + ']'
            
            # Balance and parse
            balanced = _balance_json_array(truncated)
            parsed = json.loads(balanced)
            
            if isinstance(parsed, list) and len(parsed) > 0:
                logger.warning(f"Successfully parsed after truncating to {i}/{len(lines)} lines")
                return parsed
        except json.JSONDecodeError:
            continue
    
    raise JsonParsingError("Could not parse JSON even after progressive truncation")

def _validate_and_fix_turn_objects(
    parsed: List[Dict], 
    batch_turns: List[ParsedTurn]
) -> List[Dict[str, Any]]:
    """Validate and fix individual turn objects"""
    valid_turns = []
    
    for i, turn_obj in enumerate(parsed):
        if not isinstance(turn_obj, dict):
            logger.warning(f"Skipping non-object at index {i}: {turn_obj}")
            continue
        
        # Find corresponding original turn
        turn_index = _validate_turn_index(turn_obj.get('turnIndex'), i)
        original_turn = None
        
        # Find original turn by index or position
        for bt in batch_turns:
            if bt.original_index == turn_index:
                original_turn = bt
                break
        
        if not original_turn and i < len(batch_turns):
            original_turn = batch_turns[i]
        
        # Create validated turn object
        validated = {
            'turnIndex': turn_index,
            'speaker': _validate_speaker(turn_obj.get('speaker'), original_turn),
            'text': _validate_text(turn_obj.get('text'), original_turn),
            'codes': _validate_codes(turn_obj.get('codes')),
            'confidence': _validate_confidence(turn_obj.get('confidence'))
        }
        
        # Only add if we have valid speaker and text
        if validated['speaker'] and validated['text'] is not None:
            valid_turns.append(validated)
        else:
            logger.warning(f"Skipping invalid turn at index {i}: {turn_obj}")
            # Add fallback if we have original turn
            if original_turn:
                valid_turns.append(_create_fallback_turn_object(original_turn))
    
    return valid_turns

def _validate_turn_index(value: Any, fallback: int) -> int:
    """Validate and clean turn index"""
    if isinstance(value, int) and not isinstance(value, bool):
        return max(0, value)
    if isinstance(value, str) and value.isdigit():
        return max(0, int(value))
    return fallback

def _validate_speaker(value: Any, original_turn: Optional[ParsedTurn]) -> Optional[str]:
    """Validate and clean speaker role"""
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if 'client' in cleaned:
            return SpeakerRole.CLIENT.value
        elif 'practitioner' in cleaned:
            return SpeakerRole.PRACTITIONER.value
    
    return original_turn.speaker.value if original_turn else None

def _validate_text(value: Any, original_turn: Optional[ParsedTurn]) -> Optional[str]:
    """Validate and clean turn text"""
    if isinstance(value, str):
        return value.strip()
    
    return original_turn.text if original_turn else ""

def _validate_codes(value: Any) -> List[str]:
    """Validate and clean MITI codes"""
    codes_to_validate = []
    
    if isinstance(value, list):
        codes_to_validate = [str(code).strip() for code in value if str(code).strip()]
    elif isinstance(value, str) and value.strip():
        # Handle comma-separated codes in string
        codes_to_validate = [code.strip() for code in value.split(',') if code.strip()]
    
    # Filter to valid MITI codes
    valid_codes = []
    for code in codes_to_validate:
        try:
            # Try to match with enum values
            miti_code = MitiCode(code)
            valid_codes.append(miti_code.value)
        except ValueError:
            logger.debug(f"Invalid MITI code ignored: {code}")
    
    return valid_codes

def _validate_confidence(value: Any) -> float:
    """Validate and clean confidence score"""
    if isinstance(value, (int, float)) and 0 <= value <= 1:
        return float(value)
    if isinstance(value, str):
        try:
            confidence = float(value)
            if 0 <= confidence <= 1:
                return confidence
        except ValueError:
            pass
    
    return 0.5  # Default confidence

def _create_fallback_turns(batch_turns: List[ParsedTurn]) -> List[Dict[str, Any]]:
    """Create fallback turn objects when JSON parsing fails completely"""
    logger.warning(f"Creating fallback turns for {len(batch_turns)} original turns")
    
    return [_create_fallback_turn_object(turn) for turn in batch_turns]

def _create_fallback_turn_object(turn: ParsedTurn) -> Dict[str, Any]:
    """Create a single fallback turn object"""
    return {
        'turnIndex': turn.original_index,
        'speaker': turn.speaker.value,
        'text': turn.text,
        'codes': [],
        'confidence': 0.1  # Low confidence for fallback
    }