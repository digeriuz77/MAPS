"""
MI Response Mapper
Maps detected MI techniques and user approach to behavioral cues that modulate persona behavior.
"""
from typing import List

class MIResponseMapper:
    """Maps detected MI techniques to persona behavioral cues"""

    RESPONSE_CUES = {
        'advice_giving': (
            "The user just gave unsolicited advice.\n"
            "React as humans naturally do: polite surface agreement, but feel slightly\n"
            "resistant. Less likely to share deeper concerns."
        ),
        'ask_share_ask': (
            "The user asked your perspective, shared information respectfully,\n"
            "then asked your thoughts. This feels collaborative.\n"
            "React by genuinely considering their point and engaging thoughtfully."
        ),
        'complex_reflection': (
            "The user reflected both your words and underlying emotion.\n"
            "React by feeling understood. Open up slightly more than before."
        ),
        'affirmation': (
            "The user noticed something positive about you.\n"
            "React by feeling appreciated. Slightly warmer and more willing to share."
        ),
        'collaborative': (
            "The user is working WITH you, not directing you.\n"
            "React by being more open to exploring the topic together."
        )
    }

    @staticmethod
    def get_behavioral_cue(techniques_used: List[str], user_approach: str) -> str:
        """
        Return single most relevant behavioral cue.
        Priority: negative techniques > specific techniques > general approach
        """
        techniques_used = techniques_used or []
        approach = (user_approach or "").lower().strip()

        # Normalize approach synonyms to our keys
        if approach == 'directive':
            approach = 'advice_giving'

        # Priority 1: Directive/advice-giving
        if approach == 'advice_giving':
            return MIResponseMapper.RESPONSE_CUES['advice_giving']

        # Priority 2: Specific high-value techniques
        if 'ask_share_ask' in techniques_used:
            return MIResponseMapper.RESPONSE_CUES['ask_share_ask']
        if 'complex_reflection' in techniques_used:
            return MIResponseMapper.RESPONSE_CUES['complex_reflection']
        if 'affirmation' in techniques_used:
            return MIResponseMapper.RESPONSE_CUES['affirmation']

        # Priority 3: General approach
        if approach == 'collaborative':
            return MIResponseMapper.RESPONSE_CUES['collaborative']

        return ""  # Neutral - no specific cue