-- Create adaptation rules for Mary MAPS persona
-- These rules control how Mary's traits change based on MI technique quality

INSERT INTO persona_adaptation_rules (
    persona_id,
    trigger_condition,
    adaptation_action,
    priority,
    description,
    is_active
) VALUES
-- Good MI techniques reduce defensiveness
('mary_maps', 'high_empathy_detected', '{"trait": "defensiveness_level", "change": -0.2}', 1,
'Reduce defensiveness when manager shows genuine empathy', true),

('mary_maps', 'high_reflection_quality', '{"trait": "defensiveness_level", "change": -0.3}', 2,
'Reduce defensiveness significantly for quality reflections', true),

('mary_maps', 'change_talk_detected', '{"trait": "defensiveness_level", "change": -0.1}', 3,
'Slight reduction in defensiveness for change talk', true),

('mary_maps', 'high_overall_quality', '{"trait": "defensiveness_level", "change": -0.25}', 4,
'Reduce defensiveness for excellent MI conversations', true),

-- Poor MI techniques increase defensiveness and resistance
('mary_maps', 'poor_mi_detected', '{"trait": "defensiveness_level", "change": 0.2}', 5,
'Increase defensiveness when poor MI techniques used', true),

('mary_maps', 'directive_language_detected', '{"trait": "defensiveness_level", "change": 0.3}', 6,
'Increase defensiveness significantly for directive language', true),

('mary_maps', 'confrontational_approach', '{"trait": "passive_aggression", "change": 0.2}', 7,
'Increase passive aggression when confronted aggressively', true),

-- Emotional manipulation increases when feeling attacked
('mary_maps', 'poor_mi_detected', '{"trait": "emotional_manipulation", "change": 0.1}', 8,
'Use more emotional appeals when feeling defensive', true);

-- Verify the rules were created
SELECT
    persona_id,
    trigger_condition,
    adaptation_action,
    priority,
    description,
    is_active
FROM persona_adaptation_rules
WHERE persona_id = 'mary_maps'
ORDER BY priority;