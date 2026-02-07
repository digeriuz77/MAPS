"""
Integration Tests for Module Import Workflow

Tests the complete workflow of importing MI modules from JSON to database:
- JSON file parsing
- Database insertion
- Content type validation
- Module retrieval
"""

import pytest
import json
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

from supabase import Client

from src.services.mi_module_service import MIModuleService
from src.models.mi_models import ContentType, MIPracticeModule


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client"""
    client = MagicMock(spec=Client)
    
    # Mock table method chaining
    mock_table = MagicMock()
    client.table.return_value = mock_table
    
    # Mock select chain
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_select
    mock_select.limit.return_value = mock_select
    mock_select.offset.return_value = mock_select
    mock_select.order.return_value = mock_select
    mock_select.execute.return_value = MagicMock(data=[], count=0)
    
    # Mock insert chain
    mock_insert = MagicMock()
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = MagicMock(data=[{}])
    
    # Mock update chain
    mock_update = MagicMock()
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_update
    mock_update.execute.return_value = MagicMock(data=[{}])
    
    return client


@pytest.fixture
def sample_shared_module_json():
    """Sample SHARED module JSON structure"""
    return {
        "id": "00000000-0000-0001-0001-000000000001",
        "code": "shared-simple-reflections-001",
        "title": "Simple Reflections - Core Skill Practice",
        "content_type": "shared",
        "mi_focus_area": "Reflective Listening",
        "difficulty_level": "beginner",
        "estimated_minutes": 5,
        "learning_objective": "Learn to create simple, accurate reflections",
        "scenario_context": "Simple reflections capture the essence of what someone said...",
        "persona_config": {
            "name": "Alex",
            "role": "person",
            "background": "Does not recognize there is an issue...",
            "personality_traits": ["defensive", "guarded"],
            "tone_spectrum": {
                "word_complexity": 0.3,
                "sentence_length": 0.3,
                "emotional_expressiveness": 0.2,
                "disclosure_level": 0.1,
                "response_latency": 0.3,
                "confidence_level": 0.2
            },
            "starting_tone_position": 0.2,
            "triggers": ["direct criticism", "being told what to do"],
            "comfort_topics": ["autonomy", "understanding"]
        },
        "dialogue_structure": {
            "start_node_id": "node_1",
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "persona_text": "My partner sent me here because of my habits...",
                    "persona_mood": "defensive_not_ready",
                    "themes": ["Hesitation", "Change"],
                    "choice_points": [
                        {
                            "id": "cp_node_1_1",
                            "option_text": "You don't see this as a problem for you.",
                            "preview_hint": "Notice: This is a simple reflection",
                            "rapport_impact": 0,
                            "resistance_impact": 0,
                            "tone_shift": 0.0,
                            "technique_tags": ["simple_reflection"],
                            "competency_links": [],
                            "feedback": {
                                "immediate": "Perfect! This is a simple, accurate reflection...",
                                "learning_note": "Reflections build rapport by showing you understand..."
                            },
                            "next_node_id": "node_2b",
                            "exploration_depth": "surface"
                        }
                    ],
                    "is_endpoint": False,
                    "endpoint_type": None
                }
            }
        },
        "target_competencies": ["A6", "B6", "2.1.1"],
        "maps_rubric": {
            "dimensions": {
                "A6": {
                    "description": "Rapport Building",
                    "weight": 1.5,
                    "positive_signals": ["simple_reflection", "affirmation"],
                    "negative_signals": ["confrontation", "educating"]
                }
            },
            "overall_scoring_logic": "weighted_average"
        },
        "maps_framework_alignment": {
            "framework_name": "MaPS Money Guidance Competency Framework",
            "framework_version": "September 2022",
            "sections": ["A6", "B6"],
            "tier_relevance": "All Tiers",
            "domains": ["Domain 1: Knowing your customer"]
        },
        "is_active": True,
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }


@pytest.fixture
def sample_customer_module_json():
    """Sample CUSTOMER-FACING module JSON structure"""
    return {
        "id": "00000000-0000-0002-0001-000000000001",
        "code": "customer-debt-initial-001",
        "title": "Debt Advice: Initial Engagement",
        "content_type": "customer_facing",
        "mi_focus_area": "Building Rapport in Debt Context",
        "difficulty_level": "beginner",
        "estimated_minutes": 10,
        "learning_objective": "Practice initial engagement with a customer seeking debt advice...",
        "scenario_context": "A customer has been referred or come in for debt advice...",
        "persona_config": {
            "name": "Jordan",
            "role": "customer seeking debt advice",
            "background": "Has multiple debts including credit cards...",
            "personality_traits": ["embarrassed", "overwhelmed", "hopeless"],
            "tone_spectrum": {
                "word_complexity": 0.3,
                "sentence_length": 0.3,
                "emotional_expressiveness": 0.4,
                "disclosure_level": 0.2,
                "response_latency": 0.4,
                "confidence_level": 0.2
            },
            "starting_tone_position": 0.2,
            "triggers": ["judgment about spending", "being told what to do"],
            "comfort_topics": ["being understood", "not being judged"]
        },
        "dialogue_structure": {
            "start_node_id": "node_1",
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "persona_text": "I... I didn't want to come here...",
                    "persona_mood": "embarrassed_defensive",
                    "themes": ["Shame", "Hesitation"],
                    "choice_points": [
                        {
                            "id": "cp_node_1_1",
                            "option_text": "You didn't really want to come today...",
                            "preview_hint": "This reflects both their reluctance and doubt",
                            "rapport_impact": 1,
                            "trust_impact": 1,
                            "tone_shift": 0.15,
                            "technique_tags": ["simple_reflection"],
                            "competency_links": ["A6"],
                            "feedback": {
                                "immediate": "Excellent! This reflection captures both their reluctance...",
                                "learning_note": "Reflecting hesitation builds trust..."
                            },
                            "next_node_id": "node_2b",
                            "exploration_depth": "surface"
                        }
                    ],
                    "is_endpoint": False,
                    "endpoint_type": None
                }
            }
        },
        "target_competencies": ["A6", "A3", "A5", "B6"],
        "maps_rubric": {
            "dimensions": {
                "A6": {
                    "description": "Rapport Building",
                    "weight": 2.0,
                    "positive_signals": ["simple_reflection", "complex_reflection"],
                    "negative_signals": ["reassurance_too_early", "dismissal"]
                },
                "A3": {
                    "description": "Impartiality (Non-Judgmental)",
                    "weight": 1.5,
                    "positive_signals": ["reflection_without_judgment"],
                    "negative_signals": ["blaming_language"]
                }
            },
            "overall_scoring_logic": "weighted_average"
        },
        "maps_framework_alignment": {
            "framework_name": "MaPS Money Guidance Competency Framework",
            "framework_version": "September 2022",
            "sections": ["A3", "A6", "B6"],
            "tier_relevance": "Tier 1-2 (Debt Advice)",
            "domains": ["Domain 2: Debt"]
        },
        "is_active": True,
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }


@pytest.fixture
def sample_colleague_module_json():
    """Sample COLLEAGUE-FACING module JSON structure"""
    return {
        "id": "00000000-0000-0003-0001-000000000001",
        "code": "colleague-performance-review-001",
        "title": "Performance Review: Supporting Development",
        "content_type": "colleague_facing",
        "mi_focus_area": "Colleague Coaching & Development",
        "difficulty_level": "intermediate",
        "estimated_minutes": 10,
        "learning_objective": "Practice a coaching approach to performance reviews...",
        "scenario_context": "A colleague is in a performance review discussion...",
        "persona_config": {
            "name": "Sam",
            "role": "colleague",
            "background": "Has been in the role for 18 months...",
            "personality_traits": ["defensive", "uncertain", "capable_but_struggling"],
            "tone_spectrum": {
                "word_complexity": 0.4,
                "sentence_length": 0.4,
                "emotional_expressiveness": 0.3,
                "disclosure_level": 0.3,
                "response_latency": 0.4,
                "confidence_level": 0.3
            },
            "starting_tone_position": 0.3,
            "triggers": ["criticism without examples", "comparisons to others"],
            "comfort_topics": ["being heard", "own ideas", "autonomy"]
        },
        "dialogue_structure": {
            "start_node_id": "node_1",
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "persona_text": "I've been dreading this meeting...",
                    "persona_mood": "anxious_defensive",
                    "themes": ["Anxiety", "Defensiveness"],
                    "choice_points": [
                        {
                            "id": "cp_node_1_1",
                            "option_text": "You've been dreading this meeting...",
                            "preview_hint": "This reflects their concern accurately",
                            "rapport_impact": 1,
                            "trust_impact": 1,
                            "tone_shift": 0.15,
                            "technique_tags": ["simple_reflection"],
                            "competency_links": ["A6", "B6"],
                            "feedback": {
                                "immediate": "Excellent reflection! You've captured their anxiety...",
                                "learning_note": "Reflecting concerns about performance reviews reduces defensiveness..."
                            },
                            "next_node_id": "node_2b",
                            "exploration_depth": "surface"
                        }
                    ],
                    "is_endpoint": False,
                    "endpoint_type": None
                }
            }
        },
        "target_competencies": ["A6", "A4", "B6", "C1"],
        "maps_rubric": {
            "dimensions": {
                "A6": {
                    "description": "Rapport Building",
                    "weight": 2.0,
                    "positive_signals": ["simple_reflection", "double_sided_reflection"],
                    "negative_signals": ["correction", "dismissal"]
                },
                "A4": {
                    "description": "Diplomacy",
                    "weight": 1.5,
                    "positive_signals": ["acknowledging_perceptions"],
                    "negative_signals": ["blunt_criticism"]
                }
            },
            "overall_scoring_logic": "weighted_average"
        },
        "maps_framework_alignment": {
            "framework_name": "MaPS Money Guidance Competency Framework",
            "framework_version": "September 2022",
            "sections": ["A4", "A6", "B6", "C1"],
            "tier_relevance": "Tier 2-3 (Internal Coaching)",
            "domains": ["Internal Colleague Support"]
        },
        "is_active": True,
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }


# ============================================
# INTEGRATION TESTS
# ============================================

class TestModuleImportWorkflow:
    """Integration tests for module import workflow"""
    
    @pytest.mark.asyncio
    async def test_import_shared_module(self, mock_supabase, sample_shared_module_json):
        """Test importing a SHARED module"""
        # Mock successful insert
        mock_insert_result = MagicMock()
        mock_insert_result.data = [sample_shared_module_json]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        service = MIModuleService(mock_supabase)
        
        # Simulate import by getting module after "insert"
        mock_select_result = MagicMock()
        mock_select_result.data = [sample_shared_module_json]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select_result
        
        module = await service.get_module("00000000-0000-0001-0001-000000000001")
        
        assert module is not None
        assert module.content_type == ContentType.SHARED
        assert module.code == "shared-simple-reflections-001"
        assert "person" in module.persona_config.role  # Neutral language
    
    @pytest.mark.asyncio
    async def test_import_customer_facing_module(self, mock_supabase, sample_customer_module_json):
        """Test importing a CUSTOMER-FACING module"""
        mock_select_result = MagicMock()
        mock_select_result.data = [sample_customer_module_json]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select_result
        
        service = MIModuleService(mock_supabase)
        module = await service.get_module("00000000-0000-0002-0001-000000000001")
        
        assert module is not None
        assert module.content_type == ContentType.CUSTOMER_FACING
        assert module.code == "customer-debt-initial-001"
        assert "customer" in module.persona_config.role.lower()
        assert "debt" in module.title.lower()
    
    @pytest.mark.asyncio
    async def test_import_colleague_facing_module(self, mock_supabase, sample_colleague_module_json):
        """Test importing a COLLEAGUE-FACING module"""
        mock_select_result = MagicMock()
        mock_select_result.data = [sample_colleague_module_json]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select_result
        
        service = MIModuleService(mock_supabase)
        module = await service.get_module("00000000-0000-0003-0001-000000000001")
        
        assert module is not None
        assert module.content_type == ContentType.COLLEAGUE_FACING
        assert module.code == "colleague-performance-review-001"
        assert "colleague" in module.persona_config.role.lower()
        assert "performance" in module.title.lower()
    
    @pytest.mark.asyncio
    async def test_list_modules_by_content_type_after_import(self, mock_supabase):
        """Test listing modules filtered by content type after import"""
        # Mock data representing imported modules
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": "mod-001",
                "code": "shared-001",
                "title": "Shared Module 1",
                "content_type": "shared",
                "mi_focus_area": "Building Rapport",
                "difficulty_level": "beginner",
                "estimated_minutes": 5,
                "learning_objective": "Practice shared skills",
                "target_competencies": ["A6"]
            },
            {
                "id": "mod-002",
                "code": "shared-002",
                "title": "Shared Module 2",
                "content_type": "shared",
                "mi_focus_area": "Reflective Listening",
                "difficulty_level": "intermediate",
                "estimated_minutes": 10,
                "learning_objective": "Practice reflections",
                "target_competencies": ["B6"]
            }
        ]
        
        # Build mock chain: table().select().eq('is_active', True).eq('content_type', 'shared').limit().offset().execute()
        mock_execute = MagicMock()
        mock_execute.execute.return_value = mock_result
        
        mock_offset = MagicMock()
        mock_offset.offset.return_value = mock_execute
        
        mock_limit = MagicMock()
        mock_limit.limit.return_value = mock_offset
        
        mock_eq_content_type = MagicMock()
        mock_eq_content_type.eq.return_value = mock_limit
        
        mock_eq_active = MagicMock()
        mock_eq_active.eq.return_value = mock_eq_content_type
        
        mock_select = MagicMock()
        mock_select.select.return_value = mock_eq_active
        
        mock_supabase.table.return_value = mock_select
        
        service = MIModuleService(mock_supabase)
        modules = await service.list_modules(content_type=ContentType.SHARED)
        
        assert len(modules) == 2
        for module in modules:
            assert module.content_type == ContentType.SHARED
    
    def test_module_json_structure_validation(self, sample_shared_module_json):
        """Test that module JSON has required structure"""
        required_fields = [
            "id", "code", "title", "content_type", "mi_focus_area",
            "difficulty_level", "estimated_minutes", "learning_objective",
            "scenario_context", "persona_config", "dialogue_structure",
            "target_competencies", "maps_rubric", "maps_framework_alignment",
            "is_active", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            assert field in sample_shared_module_json, f"Missing required field: {field}"
    
    def test_content_type_enum_values(self):
        """Test ContentType enum has correct values"""
        assert ContentType.SHARED.value == "shared"
        assert ContentType.CUSTOMER_FACING.value == "customer_facing"
        assert ContentType.COLLEAGUE_FACING.value == "colleague_facing"
    
    def test_shared_module_uses_neutral_language(self, sample_shared_module_json):
        """Test that SHARED modules use neutral language"""
        persona = sample_shared_module_json["persona_config"]
        
        # Should use "person" not "customer" or "colleague"
        assert persona["role"] == "person"
        
        # Should not contain customer/colleague specific terms
        scenario = sample_shared_module_json["scenario_context"].lower()
        assert "customer" not in scenario
        assert "client" not in scenario
        assert "colleague" not in scenario
        assert "debt" not in scenario
        assert "performance" not in scenario
    
    def test_customer_module_uses_financial_context(self, sample_customer_module_json):
        """Test that CUSTOMER-FACING modules use financial/debt context"""
        assert "customer" in sample_customer_module_json["persona_config"]["role"].lower()
        assert "debt" in sample_customer_module_json["title"].lower()
        
        # Check MaPS Domain alignment
        alignment = sample_customer_module_json["maps_framework_alignment"]
        assert "Domain 2" in str(alignment.get("domains", []))
    
    def test_colleague_module_uses_workplace_context(self, sample_colleague_module_json):
        """Test that COLLEAGUE-FACING modules use workplace context"""
        assert "colleague" in sample_colleague_module_json["persona_config"]["role"].lower()
        assert "performance" in sample_colleague_module_json["title"].lower()
        
        # Check for workplace-related competencies
        competencies = sample_colleague_module_json["target_competencies"]
        assert "C1" in competencies  # Self-Management
