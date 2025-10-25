"""
Aggregate statistics from coded MITI turns
"""
from typing import List, Dict
from .types import (
    AnnotatedTurn, AggregatedStats, MitiCode, SpeakerRole,
    PRACTITIONER_CODES, CLIENT_CODES, MI_ADHERENT_CODES, MI_NON_ADHERENT_CODES
)

def aggregate_miti_data(annotated_turns: List[AnnotatedTurn]) -> AggregatedStats:
    """
    Calculate aggregate statistics from annotated turns.
    
    Args:
        annotated_turns: List of turns with MITI codes
        
    Returns:
        AggregatedStats with calculated metrics
    """
    # Initialize counters
    total_turns = len(annotated_turns)
    practitioner_turns = 0
    client_turns = 0
    code_counts: Dict[str, int] = {code.value: 0 for code in MitiCode}
    code_counts["TotalReflections"] = 0
    
    # Count turns and codes
    for turn in annotated_turns:
        if turn.speaker == SpeakerRole.PRACTITIONER:
            practitioner_turns += 1
        else:
            client_turns += 1
            
        for code in turn.codes:
            code_counts[code.value] += 1
            
            # Track total reflections
            if code in [MitiCode.SR, MitiCode.CR]:
                code_counts["TotalReflections"] += 1
    
    # Calculate ratios
    reflection_to_question_ratio = _calculate_reflection_to_question_ratio(code_counts)
    percentage_complex_reflections = _calculate_complex_reflection_percentage(code_counts)
    mia_to_mina_ratio = _calculate_mia_to_mina_ratio(code_counts)
    
    return AggregatedStats(
        total_turns=total_turns,
        practitioner_turns=practitioner_turns,
        client_turns=client_turns,
        reflection_to_question_ratio=reflection_to_question_ratio,
        percentage_complex_reflections=percentage_complex_reflections,
        code_counts=code_counts,
        mia_to_mina_ratio=mia_to_mina_ratio
    )

def _calculate_reflection_to_question_ratio(code_counts: Dict[str, int]) -> str:
    """Calculate the reflection to question ratio"""
    total_reflections = code_counts.get("TotalReflections", 0)
    total_questions = code_counts.get(MitiCode.Q.value, 0)
    
    if total_questions == 0:
        if total_reflections > 0:
            return f"{total_reflections}:0"
        else:
            return "N/A"
    
    # Calculate ratio and reduce to simplest form
    from math import gcd
    divisor = gcd(total_reflections, total_questions)
    if divisor > 0:
        reflection_part = total_reflections // divisor
        question_part = total_questions // divisor
        return f"{reflection_part}:{question_part}"
    
    return f"{total_reflections}:{total_questions}"

def _calculate_complex_reflection_percentage(code_counts: Dict[str, int]) -> str:
    """Calculate percentage of complex reflections out of total reflections"""
    total_reflections = code_counts.get("TotalReflections", 0)
    complex_reflections = code_counts.get(MitiCode.CR.value, 0)
    
    if total_reflections == 0:
        return "N/A"
    
    percentage = (complex_reflections / total_reflections) * 100
    return f"{percentage:.1f}%"

def _calculate_mia_to_mina_ratio(code_counts: Dict[str, int]) -> str:
    """Calculate MI-Adherent to MI-Non-Adherent ratio"""
    # Count MI-Adherent behaviors
    mia_count = sum(
        code_counts.get(code.value, 0) 
        for code in MI_ADHERENT_CODES
    )
    
    # Count MI-Non-Adherent behaviors
    mina_count = sum(
        code_counts.get(code.value, 0) 
        for code in MI_NON_ADHERENT_CODES
    )
    
    if mina_count == 0:
        if mia_count > 0:
            return f"{mia_count}:0"
        else:
            return "N/A"
    
    # Calculate ratio and reduce to simplest form
    from math import gcd
    divisor = gcd(mia_count, mina_count)
    if divisor > 0:
        mia_part = mia_count // divisor
        mina_part = mina_count // divisor
        return f"{mia_part}:{mina_part}"
    
    return f"{mia_count}:{mina_count}"

def get_summary_statistics(stats: AggregatedStats) -> Dict[str, any]:
    """
    Get a summary of key statistics for display.
    
    Returns:
        Dictionary with formatted statistics
    """
    summary = {
        "conversation_overview": {
            "total_turns": stats.total_turns,
            "practitioner_turns": stats.practitioner_turns,
            "client_turns": stats.client_turns,
            "turn_balance": f"{stats.practitioner_turns}/{stats.client_turns}"
        },
        "mi_quality_indicators": {
            "reflection_to_question_ratio": stats.reflection_to_question_ratio,
            "complex_reflection_percentage": stats.percentage_complex_reflections,
            "mi_adherent_ratio": stats.mia_to_mina_ratio
        },
        "practitioner_behaviors": {
            "questions": stats.code_counts.get(MitiCode.Q.value, 0),
            "simple_reflections": stats.code_counts.get(MitiCode.SR.value, 0),
            "complex_reflections": stats.code_counts.get(MitiCode.CR.value, 0),
            "affirmations": stats.code_counts.get(MitiCode.AF.value, 0),
            "seeking_collaboration": stats.code_counts.get(MitiCode.SEEK.value, 0),
            "emphasizing_autonomy": stats.code_counts.get(MitiCode.EA.value, 0),
            "giving_information": stats.code_counts.get(MitiCode.GI.value, 0),
            "other": stats.code_counts.get(MitiCode.O.value, 0)
        },
        "problematic_behaviors": {
            "persuasion": stats.code_counts.get(MitiCode.PER.value, 0),
            "confrontation": stats.code_counts.get(MitiCode.C.value, 0)
        },
        "client_language": {
            "change_talk": stats.code_counts.get(MitiCode.CHANGE_TALK.value, 0),
            "sustain_talk": stats.code_counts.get(MitiCode.SUSTAIN_TALK.value, 0),
            "neutral": stats.code_counts.get(MitiCode.NEUTRAL.value, 0)
        }
    }
    
    return summary

def calculate_mi_proficiency_score(stats: AggregatedStats) -> float:
    """
    Calculate an overall MI proficiency score (0-100).
    
    This is a simplified metric for quick assessment.
    """
    score = 50.0  # Start at neutral
    
    # Positive indicators
    # Good reflection ratio (aim for 2:1 or better)
    if stats.reflection_to_question_ratio != "N/A":
        parts = stats.reflection_to_question_ratio.split(":")
        if len(parts) == 2 and int(parts[1]) > 0:
            ratio = int(parts[0]) / int(parts[1])
            if ratio >= 2:
                score += 10
            elif ratio >= 1:
                score += 5
    
    # High percentage of complex reflections (aim for >50%)
    if stats.percentage_complex_reflections != "N/A":
        percentage = float(stats.percentage_complex_reflections.rstrip("%"))
        if percentage >= 50:
            score += 10
        elif percentage >= 40:
            score += 5
    
    # Good MI-adherent ratio
    if stats.mia_to_mina_ratio != "N/A":
        parts = stats.mia_to_mina_ratio.split(":")
        if len(parts) == 2:
            mia = int(parts[0])
            mina = int(parts[1])
            if mina == 0 and mia > 0:
                score += 15
            elif mia > mina * 4:  # 4:1 or better
                score += 10
            elif mia > mina * 2:  # 2:1 or better
                score += 5
    
    # Presence of key MI behaviors
    if stats.code_counts.get(MitiCode.AF.value, 0) > 0:
        score += 5
    if stats.code_counts.get(MitiCode.EA.value, 0) > 0:
        score += 5
    if stats.code_counts.get(MitiCode.SEEK.value, 0) > 0:
        score += 5
    
    # Negative indicators
    confrontations = stats.code_counts.get(MitiCode.C.value, 0)
    if confrontations > 0:
        score -= confrontations * 5  # Each confrontation is problematic
    
    persuasions = stats.code_counts.get(MitiCode.PER.value, 0)
    if persuasions > 2:  # Some persuasion might be contextual
        score -= (persuasions - 2) * 3
    
    # Ensure score stays in bounds
    return max(0, min(100, score))
