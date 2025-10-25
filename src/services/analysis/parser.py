"""
Transcript parser for MITI analysis
"""
import re
from typing import List, Tuple, Optional, Set, Dict
from .types import (
    ParsedTurn, SpeakerRole, ParseTranscriptOutput, 
    SpeakerIdentifierHints, KNOWN_SYSTEM_SPEAKERS
)

def parse_transcript(
    raw_transcript: str,
    speaker_hints: Optional[SpeakerIdentifierHints] = None
) -> ParseTranscriptOutput:
    """
    Parse a raw transcript into structured turns with speaker identification.
    Enhanced to handle chat export formats with timestamps and metadata.
    
    Args:
        raw_transcript: The raw text of the conversation
        speaker_hints: Optional hints for identifying speakers
        
    Returns:
        ParseTranscriptOutput with parsed turns and speaker mappings
    """
    lines = raw_transcript.strip().split('\n')
    parsed_turns: List[ParsedTurn] = []
    
    # Track unique speaker strings
    unique_speakers: Set[str] = set()
    speaker_mapping: Dict[str, SpeakerRole] = {}
    
    # Extract hints if provided
    practitioner_hint = speaker_hints.practitioner_identifier_hint if speaker_hints else None
    client_hint = speaker_hints.client_identifier_hint if speaker_hints else None
    
    current_speaker = None
    current_text = []
    
    # Enhanced speaker patterns to handle chat export formats
    # Pattern 1: [timestamp] Speaker: message
    # Pattern 2: Speaker: message  
    speaker_patterns = [
        re.compile(r'^\[.*?\]\s*([A-Za-z0-9\s\-_&().]+?):\s*(.*)$'),  # Chat export format
        re.compile(r'^([A-Za-z0-9\s\-_&().]+?):\s*(.*)$')              # Simple format
    ]
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Skip metadata lines (similar to JavaScript logic)
        if (_is_metadata_line(line)):
            continue
            
        # Try to match speaker patterns
        speaker_match = None
        for pattern in speaker_patterns:
            match = pattern.match(line)
            if match:
                speaker_candidate = match.group(1).strip()
                message = match.group(2).strip()
                
                # Validate speaker name (not a timestamp or metadata)
                if _is_valid_speaker_name(speaker_candidate) and message:
                    speaker_match = (speaker_candidate, message)
                    break
        
        if speaker_match:
            # Save previous turn if exists
            if current_speaker and current_text:
                text = ' '.join(current_text).strip()
                if text and not _is_system_message(current_speaker):
                    speaker_role = _determine_speaker_role(
                        current_speaker, 
                        speaker_mapping, 
                        practitioner_hint, 
                        client_hint,
                        text
                    )
                    if speaker_role:
                        parsed_turns.append(ParsedTurn(
                            speaker=speaker_role,
                            text=text,
                            original_index=len(parsed_turns)
                        ))
                        speaker_mapping[current_speaker] = speaker_role
            
            # Start new turn
            current_speaker, message = speaker_match
            unique_speakers.add(current_speaker)
            current_text = [message] if message else []
        else:
            # Continuation of current speaker's text (if we have an active speaker)
            if current_speaker and line:
                current_text.append(line)
    
    # Don't forget the last turn
    if current_speaker and current_text:
        text = ' '.join(current_text).strip()
        if text and not _is_system_message(current_speaker):
            speaker_role = _determine_speaker_role(
                current_speaker, 
                speaker_mapping, 
                practitioner_hint, 
                client_hint,
                text
            )
            if speaker_role:
                parsed_turns.append(ParsedTurn(
                    speaker=speaker_role,
                    text=text,
                    original_index=len(parsed_turns)
                ))
                speaker_mapping[current_speaker] = speaker_role
    
    # Determine actual identifiers
    actual_practitioner = None
    actual_client = None
    
    for speaker_str, role in speaker_mapping.items():
        if role == SpeakerRole.PRACTITIONER:
            actual_practitioner = speaker_str
        elif role == SpeakerRole.CLIENT:
            actual_client = speaker_str
    
    return ParseTranscriptOutput(
        parsed_turns=parsed_turns,
        actual_practitioner_identifier=actual_practitioner,
        actual_client_identifier=actual_client,
        all_unique_speaker_strings=sorted(list(unique_speakers))
    )

def _is_metadata_line(line: str) -> bool:
    """Check if a line contains metadata that should be skipped."""
    line_lower = line.lower().strip()
    
    # Skip common metadata patterns
    metadata_patterns = [
        'date', 'session id', 'total messages',
        r'^\d+/\d+/\d+',      # Date format
        r'^\d+:\d+',         # Time format  
        r'^session-',         # Session ID
        r'^\d+$',            # Just numbers
        '--------------------------------------------------'  # Separators
    ]
    
    for pattern in metadata_patterns:
        if isinstance(pattern, str):
            if pattern in line_lower:
                return True
        else:
            if re.match(pattern, line):
                return True
    
    # Skip very short lines
    if len(line) < 3:
        return True
        
    return False

def _is_valid_speaker_name(speaker: str) -> bool:
    """Validate that a speaker name looks legitimate."""
    if not speaker or len(speaker) < 1:
        return False
        
    speaker_lower = speaker.lower()
    
    # Reject if it looks like a timestamp or metadata
    invalid_patterns = [
        r'^\d+$',           # Just numbers
        r'^\d+[:/]\d+',     # Time formats
        r'am$|pm$',         # Time suffixes
        r'date|session|total|message',  # Metadata keywords
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, speaker_lower):
            return False
            
    return True

def _is_system_message(speaker: str) -> bool:
    """Check if a speaker string represents a system message."""
    speaker_lower = speaker.lower()
    return any(sys_speaker.lower() in speaker_lower for sys_speaker in KNOWN_SYSTEM_SPEAKERS)

def _determine_speaker_role(
    speaker_string: str,
    existing_mapping: Dict[str, SpeakerRole],
    practitioner_hint: Optional[str],
    client_hint: Optional[str],
    text: str
) -> Optional[SpeakerRole]:
    """
    Determine the role of a speaker based on hints and heuristics.
    Enhanced to better handle AI persona conversations.
    """
    # Check existing mapping first
    if speaker_string in existing_mapping:
        return existing_mapping[speaker_string]
    
    speaker_lower = speaker_string.lower().strip()
    
    # Priority 1: Check explicit hints from user verification
    if practitioner_hint and practitioner_hint.lower().strip() == speaker_lower:
        return SpeakerRole.PRACTITIONER
    if client_hint and client_hint.lower().strip() == speaker_lower:
        return SpeakerRole.CLIENT
    
    # Priority 2: "You" is almost always the practitioner in MI training
    if speaker_lower == 'you':
        return SpeakerRole.PRACTITIONER
    
    # Priority 3: AI Persona patterns (these are clients in MI training)
    ai_persona_indicators = [
        'andy', 'confrontational', 'direct', 'persona', 'ai', 'bot',
        'simon', 'motivational', 'non-compliant', 'resistant', 'punky',
        'john', 'challenging', 'defensive'
    ]
    if any(indicator in speaker_lower for indicator in ai_persona_indicators):
        return SpeakerRole.CLIENT
    
    # Priority 4: Professional role indicators
    practitioner_keywords = [
        'therapist', 'counselor', 'coach', 'practitioner', 
        'doctor', 'clinician', 'provider', 'interviewer',
        'supervisor', 'manager'
    ]
    if any(keyword in speaker_lower for keyword in practitioner_keywords):
        return SpeakerRole.PRACTITIONER
    
    client_keywords = [
        'client', 'patient', 'person', 'interviewee', 'participant'
    ]
    if any(keyword in speaker_lower for keyword in client_keywords):
        return SpeakerRole.CLIENT
    
    # Priority 5: Content-based analysis
    text_lower = text.lower()
    
    # MI technique indicators (likely practitioner)
    mi_indicators = [
        'what would', 'how might', 'tell me about', 'tell me more',
        'it sounds like', 'you seem', 'i hear you', 'i understand',
        'on a scale', 'what else', 'help me understand',
        'could you say more', 'what makes you say', 'how important is it',
        'that\'s a good question', 'let\'s look into', 'i appreciate',
        'how have things been', 'what concerns you', 'i\'m sorry you feel',
        'we are discussing', 'could you expand', 'thank you'
    ]
    if any(indicator in text_lower for indicator in mi_indicators):
        return SpeakerRole.PRACTITIONER
    
    # Client resistance/confrontational patterns
    client_indicators = [
        'give me a break', 'come on', 'seriously?', 'this is bull',
        'whatever', 'you\'ve got to be kidding', 'nobody told me',
        'it\'s not my fault', 'everyone does it', 'what\'s the real deal',
        'what\'s your plan', 'what are we going to do', 'what\'s next',
        'you want to make it better', 'what else do you need'
    ]
    if any(indicator in text_lower for indicator in client_indicators):
        return SpeakerRole.CLIENT
    
    # Priority 6: If we have exactly 2 speakers and one is identified
    if len(existing_mapping) == 1:
        existing_role = list(existing_mapping.values())[0]
        return SpeakerRole.CLIENT if existing_role == SpeakerRole.PRACTITIONER else SpeakerRole.PRACTITIONER
    
    # Priority 7: Default logic for MI training scenarios
    if not existing_mapping:
        # In absence of clear indicators, first speaker is often practitioner
        # unless they show clear AI persona characteristics
        if any(indicator in speaker_lower for indicator in ai_persona_indicators):
            return SpeakerRole.CLIENT
        elif speaker_lower == 'you':
            return SpeakerRole.PRACTITIONER
        elif any(indicator in text_lower for indicator in mi_indicators):
            return SpeakerRole.PRACTITIONER
        else:
            # Conservative default - let explicit verification handle this
            return SpeakerRole.PRACTITIONER
    
    return None

def validate_transcript(parsed_output: ParseTranscriptOutput) -> Tuple[bool, List[str]]:
    """
    Validate that the parsed transcript meets basic requirements.
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    warnings = []
    
    if not parsed_output.parsed_turns:
        issues.append("No valid conversational turns found")
        
    if not parsed_output.actual_practitioner_identifier:
        issues.append("Could not identify practitioner speaker")
        
    if not parsed_output.actual_client_identifier:
        issues.append("Could not identify client speaker")
    
    # Check for minimum conversation length - be more flexible
    if len(parsed_output.parsed_turns) < 2:
        issues.append(f"Conversation too short ({len(parsed_output.parsed_turns)} turns). Need at least 2 turns for analysis.")
    elif len(parsed_output.parsed_turns) < 4:
        warnings.append(f"Short conversation ({len(parsed_output.parsed_turns)} turns). Analysis quality may be limited with fewer than 4 turns.")
    
    # Check for speaker balance
    practitioner_turns = sum(1 for turn in parsed_output.parsed_turns 
                           if turn.speaker == SpeakerRole.PRACTITIONER)
    client_turns = sum(1 for turn in parsed_output.parsed_turns 
                      if turn.speaker == SpeakerRole.CLIENT)
    
    if practitioner_turns == 0:
        issues.append("No practitioner turns found")
    if client_turns == 0:
        issues.append("No client turns found")
    
    # Only critical issues prevent analysis
    is_valid = len(issues) == 0
    
    # Combine issues and warnings for reporting
    all_issues = issues + [f"Warning: {w}" for w in warnings]
    
    return is_valid, all_issues
