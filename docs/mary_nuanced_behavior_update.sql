-- Make Mary more nuanced - she withholds information and makes managers work for it
UPDATE personas
SET
  -- Add information disclosure patterns
  mi_response_patterns = jsonb_set(
    mi_response_patterns,
    '{information_disclosure}',
    '{
      "initial_response": "deflect_or_minimal",
      "after_pressure": "reluctant_partial_disclosure",
      "after_empathy": "gradual_opening",
      "after_multiple_questions": "defensive_full_disclosure"
    }'
  ),

  -- Add question response patterns
  mi_response_patterns = jsonb_set(
    mi_response_patterns,
    '{question_responses}',
    '{
      "direct_questions": "deflect_with_excuse",
      "follow_up_questions": "minimal_grudging_answer",
      "empathetic_questions": "more_detailed_response",
      "aggressive_questions": "shut_down_or_anger"
    }'
  ),

  -- Enhanced communication patterns for information control
  communication_style = jsonb_set(
    communication_style,
    '{information_sharing}',
    '{
      "initial_disclosure": "surface_level_only",
      "requires_coaxing": true,
      "deflection_before_truth": true,
      "emotional_barriers": ["fear_of_judgment", "professional_pride", "family_privacy"]
    }'
  ),

  -- Add psychological barriers
  language_markers = jsonb_set(
    language_markers,
    '{deflection_phrases}',
    '[
      "It''s complicated",
      "There''s more to it than that",
      "I''d rather not get into it",
      "That''s personal",
      "It''s not really relevant",
      "I don''t think you''d understand"
    ]'
  ),

  -- Add reluctant disclosure phrases
  language_markers = jsonb_set(
    language_markers,
    '{reluctant_disclosure}',
    '[
      "Well, if you must know...",
      "I suppose I should mention...",
      "Look, this is difficult to talk about...",
      "I wasn''t going to say anything, but...",
      "Since you''re pushing for details..."
    ]'
  ),

  -- Add information layers - what she reveals when
  metadata = jsonb_set(
    metadata,
    '{information_layers}',
    '{
      "layer_1_surface": ["call_volume_down", "been_distracted_lately", "personal_stuff_going_on"],
      "layer_2_work_impact": ["taking_longer_breaks", "hard_to_concentrate", "stress_affecting_performance"],
      "layer_3_family_hints": ["issues_at_home", "family_responsibilities", "childcare_challenges"],
      "layer_4_specific_details": ["son_school_problems", "single_parent_struggles", "school_calling_during_work"],
      "layer_5_emotional_core": ["feeling_torn", "guilt_about_work", "fear_of_losing_job", "exhaustion"]
    }'
  ),

  -- Add disclosure triggers - what makes her open up
  metadata = jsonb_set(
    metadata,
    '{disclosure_triggers}',
    '{
      "empathy_responses": ["I can see this is difficult", "That sounds really challenging", "You''re juggling a lot"],
      "non_judgmental_questions": ["Help me understand", "What''s that like for you", "How has that been"],
      "validation_statements": ["That must be hard", "Many parents face this", "You''re doing your best"],
      "privacy_respect": ["You don''t have to share if you''re not comfortable", "Only if you want to talk about it"]
    }'
  )'
WHERE persona_id = 'mary_maps';

-- Verify the complex structure
SELECT
  persona_id,
  mi_response_patterns->'information_disclosure' as info_disclosure,
  metadata->'information_layers' as info_layers,
  language_markers->'deflection_phrases' as deflection_phrases
FROM personas
WHERE persona_id = 'mary_maps';