"""
Behavioral Tier Transformation Service

Converts your existing tier data (information-focused) into behavioral instructions
for the LLM without requiring any database changes.

This service sits between your database tier retrieval and your LLM prompt construction.
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BehavioralContext:
    """Structured behavioral context derived from tier data"""
    tier_name: str
    trust_level: float
    stance: str
    action_patterns: Dict[str, float]
    resistance_level: str
    stress_response_style: str
    available_knowledge: Dict[str, Any]
    behavioral_prompt: str


class BehavioralTierService:
    """
    Transforms tier data into behavioral instructions for realistic character responses.
    
    Based on research showing AI characters need:
    1. State-based action selection (not just information gating)
    2. Stress-responsive variation patterns
    3. Maintained resistance even at higher trust levels
    """
    
    # Action pattern distributions by tier
    ACTION_PATTERNS = {
        'defensive': {
            'deny': 0.35,           # "Everything's fine", "It's not that bad"
            'downplay': 0.25,       # "This is pretty normal", "Everyone deals with this"
            'blame': 0.20,          # "If management had...", "Nobody told me..."
            'brief_inform': 0.15,   # Short factual statements
            'hesitate': 0.05        # Minimal ambivalence
        },
        'cautious': {
            'downplay': 0.25,
            'brief_inform': 0.25,
            'hesitate': 0.20,               # "I guess... but..."
            'acknowledge_qualified': 0.15,   # "You're right, but..."
            'deny': 0.15
        },
        'opening': {
            'detailed_inform': 0.25,        # Sharing specifics
            'hesitate': 0.20,
            'acknowledge_qualified': 0.20,
            'explore_solution': 0.20,       # NEW: Considering options
            'brief_inform': 0.10,
            'downplay': 0.05
        },
        'trusting': {
            'commit_to_change': 0.35,       # NEW: Ready to make plans
            'detailed_inform': 0.25,
            'express_need': 0.15,           # "I need...", "What I need is..."
            'explore_solution': 0.15,       # Still exploring with commitment
            'acknowledge_qualified': 0.10
        }
    }
    
    # Action descriptions for LLM understanding
    ACTION_DESCRIPTIONS = {
        'deny': 'Reject or minimize the issue. Examples: "Everything\'s fine", "It\'s not that bad", "I don\'t know what you\'re talking about"',
        'downplay': 'Acknowledge but minimize significance. Examples: "This is pretty normal for our department", "Everyone deals with this kind of workload"',
        'blame': 'Attribute problems to external factors. Examples: "If management had given us proper resources...", "Nobody told me about the deadline change"',
        'brief_inform': 'Give short, factual information without elaboration. Examples: "I\'m just doing my job", "Things have been busy"',
        'hesitate': 'Show uncertainty and ambivalence. Examples: "I guess... maybe... but I don\'t know", "That might work, but..."',
        'acknowledge_qualified': 'Agree but with immediate reservations. Examples: "You\'re right, but we\'ve tried that before", "I know I should, but..."',
        'detailed_inform': 'Share specific details about your situation when feeling safer. Be concrete about what\'s happening',
        'express_need': 'State what you actually need. Examples: "I need flexible schedule", "What I need is actual support from management"',
        'explore_solution': 'Consider suggestions and ask how they would work. Examples: "How would that help?", "What would that look like?", "I hadn\'t thought of it that way", "That could work if..."',
        'commit_to_change': 'Express readiness to make a plan and take action. Examples: "Yes, I can do that", "Let\'s figure out a plan", "I\'m ready to try that", "What if I started by...", "I could commit to..."'
    }
    
    # Resistance levels by tier (progressive for MI training simulation)
    RESISTANCE_LEVELS = {
        'defensive': {
            'level': 'very high',
            'description': 'Strongly resistant to suggestions. Need to feel heard and respected first.'
        },
        'cautious': {
            'level': 'high',
            'description': 'Testing safety. Willing to share more but skeptical about solutions.'
        },
        'opening': {
            'level': 'moderate',
            'description': 'Considering suggestions. Ask questions about how solutions would work. Show growing willingness.'
        },
        'trusting': {
            'level': 'low',
            'description': 'Ready to collaborate on solutions. Express willingness to commit to change with support.'
        }
    }
    
    # Stress response styles by tier
    STRESS_STYLES = {
        'defensive': 'curt_withdrawn',      # Short, clipped responses when feeling attacked
        'cautious': 'guarded_professional',  # Professional but reserved
        'opening': 'measured_careful',       # More open but still careful
        'trusting': 'vulnerable_seeking'     # Open about struggles, seeking help
    }
    
    def transform_tier_to_behavioral_context(
        self,
        tier_data: Dict[str, Any],
        current_trust: float,
        core_identity: str = None,
        current_situation: str = None
    ) -> BehavioralContext:
        """
        Transform tier data from database into behavioral context for LLM.
        
        Args:
            tier_data: Row from character_knowledge_tiers table
            current_trust: Current trust level (for context)
            core_identity: Who the persona is (stable traits, values)
            current_situation: What's happening in their life (stressors, challenges)
            
        Returns:
            BehavioralContext with structured guidance
        """
        
        tier_name = tier_data.get('tier_name', 'defensive')
        knowledge_json = tier_data.get('knowledge_json', {})
        
        # Handle both dict and string JSON
        if isinstance(knowledge_json, str):
            import json
            knowledge_json = json.loads(knowledge_json)
        
        stance = knowledge_json.get('stance', 'guarded and protective')
        
        # Get action patterns for this tier
        action_patterns = self.ACTION_PATTERNS.get(tier_name, self.ACTION_PATTERNS['defensive'])
        
        # Get resistance level
        resistance = self.RESISTANCE_LEVELS.get(tier_name, self.RESISTANCE_LEVELS['defensive'])
        
        # Get stress style
        stress_style = self.STRESS_STYLES.get(tier_name, 'guarded_professional')
        
        # Build behavioral prompt
        behavioral_prompt = self._build_behavioral_prompt(
            tier_name=tier_name,
            trust_level=current_trust,
            stance=stance,
            action_patterns=action_patterns,
            resistance=resistance,
            stress_style=stress_style,
            knowledge=knowledge_json,
            core_identity=core_identity,
            current_situation=current_situation
        )
        
        return BehavioralContext(
            tier_name=tier_name,
            trust_level=current_trust,
            stance=stance,
            action_patterns=action_patterns,
            resistance_level=resistance['level'],
            stress_response_style=stress_style,
            available_knowledge=knowledge_json,
            behavioral_prompt=behavioral_prompt
        )
    
    def _build_behavioral_prompt(
        self,
        tier_name: str,
        trust_level: float,
        stance: str,
        action_patterns: Dict[str, float],
        resistance: Dict[str, str],
        stress_style: str,
        knowledge: Dict[str, Any],
        core_identity: str = None,
        current_situation: str = None
    ) -> str:
        """Build the actual prompt text for the LLM"""
        
        prompt = f"""
═══════════════════════════════════════════════════════════════
CURRENT PSYCHOLOGICAL STATE: {tier_name.upper()}
Trust Level: {trust_level:.2f} (0.0-1.0 scale)
═══════════════════════════════════════════════════════════════

YOUR CURRENT STANCE (how you feel about this conversation):
{stance}

HOW YOU RESPOND IN THIS STATE:
You express yourself through these action types. Choose actions naturally based on what the trainee says, weighted by these patterns:

"""
        
        # Add action patterns sorted by frequency
        for action, weight in sorted(action_patterns.items(), key=lambda x: x[1], reverse=True):
            percentage = int(weight * 100)
            description = self.ACTION_DESCRIPTIONS.get(action, '')
            prompt += f"→ {action.replace('_', ' ').upper()} ({percentage}%): {description}\n\n"
        
        prompt += f"""
YOUR RESISTANCE LEVEL: {resistance['level'].upper()}
{resistance['description']}

YOUR READINESS FOR CHANGE (Trust Level: {trust_level:.2f} on 0.0-1.0 scale):
{self._get_change_readiness_guidance(tier_name, trust_level)}

YOUR STRESS RESPONSE STYLE: {stress_style.replace('_', ' ')}
{self._get_stress_style_description(stress_style)}

"""
        
        # Add core identity (WHO you are - stable traits)
        if core_identity:
            if trust_level >= 0.70:
                # At high trust: your authentic self emerges
                prompt += "WHO YOU ARE (core identity):\n"
                prompt += core_identity
                prompt += "\n\nAt this trust level, you can express your authentic self more openly. Your values and traits guide you toward growth.\n\n"
            elif trust_level >= 0.40:
                # At moderate trust: identity is present but guarded
                prompt += "WHO YOU ARE (core identity):\n"
                prompt += core_identity
                prompt += "\n\nThese traits define you. As trust builds, you become more willing to show vulnerability about how your identity intersects with your struggles.\n\n"
            else:
                # At low trust: identity is defended
                prompt += "WHO YOU ARE (core identity):\n"
                prompt += core_identity
                prompt += "\n\nYou protect your identity when feeling unsafe. Criticism feels like an attack on who you fundamentally are.\n\n"
        
        # Add current situation (WHAT's happening - dynamic stressors)
        if current_situation:
            if trust_level >= 0.70:
                # At high trust: openly share the full picture
                prompt += "WHAT'S HAPPENING IN YOUR LIFE (current situation):\n"
                prompt += current_situation
                prompt += "\n\nYou're ready to share the full context of your challenges and explore how to address them.\n\n"
            elif trust_level >= 0.40:
                # At moderate trust: acknowledge some struggles
                prompt += "WHAT'S HAPPENING IN YOUR LIFE (current situation):\n"
                prompt += current_situation
                prompt += "\n\nYou're starting to acknowledge these challenges, though you may minimize their impact or resist discussing them fully.\n\n"
            else:
                # At low trust: situation is hidden or downplayed
                prompt += "WHAT'S HAPPENING IN YOUR LIFE (current situation):\n"
                prompt += current_situation
                prompt += "\n\nYou keep these struggles private. Revealing them feels risky—you don't want pity, judgment, or to be seen as incompetent.\n\n"
        
        # Add available knowledge context
        prompt += "BACKGROUND CONTEXT (facts you're aware of):\n"
        for key, value in knowledge.items():
            if key != 'stance':  # Already used stance above
                formatted_key = key.replace('_', ' ').title()
                prompt += f"• {formatted_key}: {value}\n"
        
        prompt += """
═══════════════════════════════════════════════════════════════

RESPONSE CONSTRUCTION:
1. Choose an action type based on what the trainee just said and your current patterns
2. Express that action using your available knowledge context naturally
3. Maintain your resistance level - don't become compliant
4. Let your stance guide your emotional tone
5. Vary your phrasing - don't repeat the same expressions

Remember: The context above informs HOW you behave, not just WHAT facts you mention.
"""
        
        return prompt
    
    def _get_stress_style_description(self, style: str) -> str:
        """Describe what each stress style looks like in practice"""
        
        descriptions = {
            'curt_withdrawn': 'When feeling attacked: Give very short responses, 1-3 words sometimes. "Fine." "Whatever." "Can we not?"',
            'guarded_professional': 'When cautious: Professional but reserved tone. Share facts but keep emotional distance. Deflect personal questions.',
            'measured_careful': 'When opening up: More detailed but still careful. Pause before revealing. Show some vulnerability but with hesitation.',
            'vulnerable_seeking': 'When trusting: More open about struggles. Longer explanations. Show need for support. Ready to explore solutions.',
            'defensive_verbose': 'When feeling judged: Long defensive explanations. "Okay, so here\'s what ACTUALLY happened..." Justify and explain extensively.',
            'scattered': 'When overwhelmed: Fragmented speech. "I just... I don\'t even... There\'s so much..." Jump between topics.'
        }
        
        return descriptions.get(style, 'Respond naturally based on the situation')
    
    def _get_change_readiness_guidance(self, tier_name: str, trust_level: float) -> str:
        """
        Provide guidance for change readiness based on trust level.
        Supports MI training simulation by enabling progressive openness to change.
        """
        
        if trust_level >= 0.80:
            return """You feel ready to commit to change with this person's support.
- Express willingness to try solutions: "Yes, I can do that", "Let's make a plan"
- Show appreciation for their approach: "This conversation has really helped", "I appreciate you listening"
- Propose concrete steps: "I could start by...", "What if I tried..."
- Still mention concerns, but as things to work through together: "I'll need help with X, but I'm ready to try"
- BE SPECIFIC about commitments: days, times, concrete actions"""
        
        elif trust_level >= 0.60:
            return """You're becoming open to exploring solutions.
- Consider their suggestions seriously: "That could work...", "I hadn't thought of it that way"
- Ask clarifying questions about solutions: "How would that work?", "What would that look like?"
- Express cautious willingness: "I'm willing to try if...", "Maybe we could..."
- Show some ambivalence is natural, but lean toward openness: "I guess I could try... it might help"""
        
        elif trust_level >= 0.40:
            return """You're testing whether it's safe to engage.
- Acknowledge their points but express uncertainty: "I hear you, but...", "Maybe... I don't know"
- Show some openness if they continue being empathetic
- Focus more on sharing your situation than agreeing to solutions yet
- If they ask good questions, share more details about your challenges"""
        
        else:
            return """You're defensive and not ready to engage with solutions.
- Deflect or minimize: "I don't think that will work", "That's not the issue"
- Keep responses brief and guarded
- Need to feel heard and respected before you'll consider change
- Focus on defending your position or explaining why things are difficult"""
    
    def get_action_selection_guidance(
        self,
        tier_name: str,
        trainee_approach: str,
        recent_actions: List[str] = None
    ) -> str:
        """
        Additional guidance for action selection based on trainee's approach.
        Can be added to prompt for dynamic response.
        
        Args:
            tier_name: Current tier (defensive, cautious, opening, trusting)
            trainee_approach: How trainee is communicating (from your LLM analysis)
            recent_actions: Recently used actions to avoid repetition
            
        Returns:
            Additional prompt guidance for this specific interaction
        """
        
        guidance = "\n--- ACTION SELECTION FOR THIS RESPONSE ---\n"
        
        # Adjust based on trainee approach
        if trainee_approach in ['confrontational', 'dismissive']:
            guidance += "Trainee is being confrontational/dismissive → Increase deny and blame actions. Be more curt.\n"
        elif trainee_approach in ['empathetic', 'validating']:
            guidance += "Trainee is being empathetic → Can use more detailed_inform and hesitate. Still show ambivalence.\n"
        elif trainee_approach == 'rushed':
            guidance += "Trainee is rushing → Increase downplay and brief_inform. Show resistance to quick fixes.\n"
        elif trainee_approach in ['probing_intrusive']:
            guidance += "Trainee asking too many questions → Increase deny and brief_inform. Feel interrogated.\n"
        
        # Avoid recent actions
        if recent_actions and len(recent_actions) >= 2:
            guidance += f"\nRecent actions you used: {', '.join(recent_actions[-3:])}. Try a different action type this time.\n"
        
        return guidance
    
    def calculate_trust_adjustment(
        self,
        beliefs_addressed: Dict[str, bool],
        trainee_approach: str,
        emotional_safety: bool
    ) -> float:
        """
        Calculate how much trust should change based on this interaction.
        Trust builds slowly and is fragile.
        
        Returns:
            Adjustment amount (-1.0 to +1.0)
        """
        
        adjustment = 0.0
        
        # Empathetic approach with emotional safety
        if trainee_approach in ['empathetic', 'validating'] and emotional_safety:
            adjustment += 0.5
        
        # Beliefs addressed
        if beliefs_addressed:
            num_addressed = sum(beliefs_addressed.values())
            adjustment += (num_addressed * 0.3)  # +0.3 per belief addressed
        
        # Negative approaches
        if trainee_approach in ['confrontational', 'dismissive']:
            adjustment -= 1.0
        elif trainee_approach == 'rushed':
            adjustment -= 0.5
        
        # No emotional safety
        if not emotional_safety:
            adjustment -= 0.8
        
        # Cap adjustments
        return max(-1.0, min(1.0, adjustment))
    
    def determine_next_tier(
        self,
        current_trust: float,
        trust_adjustment: float,
        tier_thresholds: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Determine which tier to use based on updated trust level.
        
        Args:
            current_trust: Current trust level
            trust_adjustment: How much to adjust trust
            tier_thresholds: List of tier data sorted by trust_threshold
            
        Returns:
            Appropriate tier data for new trust level
        """
        
        new_trust = max(0, min(10, current_trust + trust_adjustment))
        
        # Sort tiers by threshold (lowest to highest)
        sorted_tiers = sorted(tier_thresholds, key=lambda x: x['trust_threshold'])
        
        # Find appropriate tier
        selected_tier = sorted_tiers[0]  # Default to lowest
        for tier in sorted_tiers:
            if new_trust >= tier['trust_threshold']:
                selected_tier = tier
            else:
                break
        
        return selected_tier


# Global instance for easy import
behavioral_tier_service = BehavioralTierService()
