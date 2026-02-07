"""
MI Practice Integration Tests

Tests for MI Practice API endpoints to verify the complete module workflow:
- Module listing and retrieval
- Starting attempts
- Making choices
- Completing attempts
- Progress tracking
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the router and dependencies
from src.api.routes.mi_practice import router as mi_practice_router
from src.models.mi_models import (
    MIPracticeModule,
    MIPracticeModuleSummary,
    MIPracticeAttempt,
    StartAttemptResponse,
    MakeChoiceResponse,
    FinalScores,
    CompletionStatus,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    client = MagicMock()
    return client


@pytest.fixture
def mock_module_service():
    """Create a mock module service"""
    service = MagicMock()
    
    # Mock list_modules - returns coroutine for async compatibility
    async def mock_list_modules(*args, **kwargs):
        return [
            MIPracticeModuleSummary(
                id="mod-001",
                code="mi-building-rapport-001",
                title="Building Rapport with Alex",
                content_type="shared",
                mi_focus_area="Building Rapport",
                difficulty_level="beginner",
                estimated_minutes=5,
                learning_objective="Practice establishing rapport with a hesitant team member",
                target_competencies=["A6", "B6"],
                user_attempts=0,
                best_score=None,
                is_completed=False,
            ),
            MIPracticeModuleSummary(
                id="mod-002",
                code="mi-explore-resistance-001",
                title="Exploring Resistance with Jordan",
                content_type="shared",
                mi_focus_area="Exploring Resistance",
                difficulty_level="intermediate",
                estimated_minutes=8,
                learning_objective="Practice responding to defensive statements",
                target_competencies=["A6", "B6", "1.2.1"],
                user_attempts=2,
                best_score=8.5,
                is_completed=True,
            ),
        ]
    
    service.list_modules = MagicMock(side_effect=mock_list_modules)
    
    # Mock get_module - async version
    async def mock_get_module(*args, **kwargs):
        return MIPracticeModule(
        id="mod-001",
        code="mi-building-rapport-001",
        title="Building Rapport with Alex",
        mi_focus_area="Building Rapport",
        difficulty_level="beginner",
        estimated_minutes=5,
        learning_objective="Practice establishing rapport with a hesitant team member",
        scenario_context="Alex is a new team member who seems reserved...",
        persona_config={
            "name": "Alex",
            "role": "team member",
            "background": "Recently joined the team, feeling uncertain",
            "personality_traits": ["reserved", "thoughtful"],
            "tone_spectrum": {
                "word_complexity": 0.5,
                "sentence_length": 0.5,
                "emotional_expressiveness": 0.3,
                "disclosure_level": 0.2,
                "response_latency": 0.5,
                "confidence_level": 0.4,
            },
            "starting_tone_position": 0.2,
            "triggers": ["direct criticism"],
            "comfort_topics": ["growth opportunities"],
        },
        dialogue_structure={
            "start_node_id": "node_1",
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "persona_text": "I'm not sure why we're meeting. Is this about my performance?",
                    "persona_mood": "defensive_guarded",
                    "themes": ["Trust"],
                    "choice_points": [
                        {
                            "id": "cp_1_open",
                            "option_text": "Thanks for coming in. I wanted to check in about how things are going.",
                            "preview_hint": "Open, appreciative invitation",
                            "rapport_impact": 1,
                            "resistance_impact": -1,
                            "tone_shift": 0.1,
                            "technique_tags": ["open_question", "rapport_building"],
                            "competency_links": ["A6", "B6"],
                            "feedback": {
                                "immediate": "Starting with appreciation helps establish safety.",
                                "learning_note": "Open questions invite the person to share their perspective.",
                            },
                            "next_node_id": "node_2_open",
                            "exploration_depth": "surface",
                        },
                        {
                            "id": "cp_1_direct",
                            "option_text": "Yes, I have some concerns about your recent work.",
                            "preview_hint": "Direct approach",
                            "rapport_impact": -2,
                            "resistance_impact": 2,
                            "tone_shift": -0.2,
                            "technique_tags": ["direct_statement"],
                            "competency_links": [],
                            "feedback": {
                                "immediate": "Starting with concerns can increase defensiveness.",
                                "learning_note": "Consider starting with rapport building before addressing concerns.",
                            },
                            "next_node_id": "node_2_defensive",
                            "exploration_depth": "surface",
                        },
                    ],
                    "is_endpoint": False,
                },
                "node_2_open": {
                    "id": "node_2_open",
                    "persona_text": "Oh, I see. I guess I've been a bit overwhelmed lately.",
                    "persona_mood": "cautious_open",
                    "themes": ["Overwhelm"],
                    "choice_points": [],
                    "is_endpoint": True,
                    "endpoint_type": "positive",
                },
                "node_2_defensive": {
                    "id": "node_2_defensive",
                    "persona_text": "I knew it. Everyone's always criticizing me.",
                    "persona_mood": "defensive_closed",
                    "themes": ["Defensiveness"],
                    "choice_points": [],
                    "is_endpoint": True,
                    "endpoint_type": "negative",
                },
            },
        },
        target_competencies=["A6", "B6"],
        maps_rubric={
            "dimensions": {
                "A6": {
                    "description": "Rapport Building",
                    "weight": 1.5,
                    "positive_signals": ["open_questions", "affirmations"],
                    "negative_signals": ["confrontation"],
                },
            },
            "overall_scoring_logic": "weighted_average",
        },
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    service.get_module = MagicMock(side_effect=mock_get_module)
    
    async def mock_get_focus_areas(*args, **kwargs):
        return [
            "Building Rapport",
            "Exploring Resistance", 
            "Action Planning",
            "Eliciting Change Talk",
            "Affirming",
            "Reflective Listening",
        ]
    
    service.get_focus_areas = MagicMock(side_effect=mock_get_focus_areas)
    
    async def mock_get_difficulty_levels(*args, **kwargs):
        return ["beginner", "intermediate", "advanced"]
    
    service.get_difficulty_levels = MagicMock(side_effect=mock_get_difficulty_levels)
    
    return service


@pytest.fixture
def mock_attempt_service():
    """Create a mock attempt service"""
    service = MagicMock()
    
    # Mock start_attempt - async version
    async def mock_start_attempt(*args, **kwargs):
        return StartAttemptResponse(
            attempt_id="attempt-001",
            module_id="mod-001",
            module_code="mi-building-rapport-001",
            module_title="Building Rapport with Alex",
            current_state={
                "node_id": "node_1",
                "persona_text": "I'm not sure why we're meeting. Is this about my performance?",
                "persona_mood": "defensive_guarded",
                "themes": ["Trust"],
            },
            choice_points=[
                {
                    "id": "cp_1_open",
                    "option_text": "Thanks for coming in. I wanted to check in about how things are going.",
                    "preview_hint": "Open, appreciative invitation",
                },
                {
                    "id": "cp_1_direct",
                    "option_text": "Yes, I have some concerns about your recent work.",
                    "preview_hint": "Direct approach",
                },
            ],
            learning_objective="Practice establishing rapport with a hesitant team member",
        )
    
    service.start_attempt = MagicMock(side_effect=mock_start_attempt)
    
    # Mock make_choice - async version
    async def mock_make_choice(*args, **kwargs):
        return MakeChoiceResponse(
        attempt_id="attempt-001",
        turn_number=1,
        choice_made={
            "node_id": "node_1",
            "choice_point_id": "cp_1_open",
            "techniques_used": ["open_question", "rapport_building"],
            "competencies_demonstrated": ["A6", "B6"],
        },
        feedback={
            "immediate": "Starting with appreciation helps establish safety.",
            "learning_note": "Open questions invite the person to share their perspective.",
            "technique_analysis": {
                "open_question": "Used effectively to invite sharing",
            },
        },
        new_state={
            "node_id": "node_2_open",
            "persona_text": "Oh, I see. I guess I've been a bit overwhelmed lately.",
            "persona_mood": "cautious_open",
            "themes": ["Overwhelm"],
            "rapport_score": 1,
            "resistance_level": 4,
            "tone_position": 0.3,
        },
        next_choice_points=[],
        is_complete=True,
    )
    
    service.make_choice = MagicMock(side_effect=mock_make_choice)
    
    # Mock get_attempt - async version
    async def mock_get_attempt(*args, **kwargs):
        return MIPracticeAttempt(
        id="attempt-001",
        user_id="user-001",
        module_id="mod-001",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        current_node_id="node_2_open",
        path_taken=["node_1", "node_2_open"],
        current_rapport_score=1,
        current_resistance_level=4,
        tone_spectrum_position=0.3,
        choices_made=[
            {
                "node_id": "node_1",
                "choice_point_id": "cp_1_open",
                "chosen_at": datetime.utcnow().isoformat(),
                "rapport_impact": 1,
                "resistance_impact": -1,
                "tone_shift": 0.1,
                "techniques_used": ["open_question", "rapport_building"],
                "competencies_demonstrated": ["A6", "B6"],
            },
        ],
        completion_status=CompletionStatus.COMPLETED,
        final_scores=FinalScores(
            overall_score=8.5,
            competency_scores={"A6": 9.0, "B6": 8.0},
            technique_counts={"open_question": 1, "rapport_building": 1},
            resistance_triggered=0,
            rapport_built=True,
            final_tone_position=0.3,
        ),
        insights_generated=[
            {
                "type": "positive",
                "description": "Good use of open questions to build rapport",
            },
        ],
    )
    
    service.get_attempt = MagicMock(side_effect=mock_get_attempt)
    
    # Mock complete_attempt - async version
    async def mock_complete_attempt(*args, **kwargs):
        return MIPracticeAttempt(
        id="attempt-001",
        user_id="user-001",
        module_id="mod-001",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        current_node_id="node_2_open",
        path_taken=["node_1", "node_2_open"],
        current_rapport_score=1,
        current_resistance_level=4,
        tone_spectrum_position=0.3,
        choices_made=[],
        completion_status=CompletionStatus.COMPLETED,
        final_scores=FinalScores(
            overall_score=8.5,
            competency_scores={"A6": 9.0, "B6": 8.0},
            technique_counts={"open_question": 1, "rapport_building": 1},
            resistance_triggered=0,
            rapport_built=True,
            final_tone_position=0.3,
        ),
        insights_generated=[],
    )
    
    service.complete_attempt = MagicMock(side_effect=mock_complete_attempt)
    
    return service


@pytest.fixture
def mock_progress_service():
    """Create a mock progress service"""
    service = MagicMock()
    
    # Mock get_progress_response - async version
    async def mock_get_progress_response(*args, **kwargs):
        return {
            "modules_completed": 5,
            "modules_attempted": 8,
            "total_practice_minutes": 45,
            "overall_progress_percent": 62.5,
            "competency_scores": {
                "A6": {"current": 8.5, "trend": "improving", "attempts": 5},
                "B6": {"current": 7.8, "trend": "stable", "attempts": 5},
            },
            "techniques_practiced": {
                "open_question": {"count": 12, "avg_quality": 8.2},
                "affirmation": {"count": 8, "avg_quality": 7.5},
            },
            "recent_attempts": [
                {
                    "attempt_id": "attempt-001",
                    "module_title": "Building Rapport with Alex",
                    "completed_at": datetime.utcnow().isoformat(),
                    "score": 8.5,
                },
            ],
            "learning_insights": [
                {
                    "type": "strength",
                    "description": "You're showing strong rapport building skills",
                },
            ],
        }
    service.get_progress_response = MagicMock(side_effect=mock_get_progress_response)
    
    # Mock get_competency_breakdown
    async def mock_get_competency_breakdown(*args, **kwargs):
        return {
        "A6": {
            "current_score": 8.5,
            "trend": "improving",
            "attempts": 5,
            "history": [7.0, 7.5, 8.0, 8.2, 8.5],
        },
        "B6": {
            "current_score": 7.8,
            "trend": "stable",
            "attempts": 5,
            "history": [7.5, 7.8, 7.9, 7.7, 7.8],
        },
    }
    
    service.get_competency_breakdown = MagicMock(side_effect=mock_get_competency_breakdown)
    
    # Mock update_progress_after_attempt
    async def mock_update_progress_after_attempt(*args, **kwargs):
        return True
    service.update_progress_after_attempt = MagicMock(side_effect=mock_update_progress_after_attempt)
    
    return service


@pytest.fixture
def test_app(mock_module_service, mock_attempt_service, mock_progress_service):
    """Create a test FastAPI app with mocked dependencies"""
    app = FastAPI()
    
    # Override dependencies
    def override_get_mi_module_service():
        return mock_module_service
    
    def override_get_mi_attempt_service():
        return mock_attempt_service
    
    def override_get_mi_progress_service():
        return mock_progress_service
    
    # Import and override
    from src.dependencies import (
        get_mi_module_service,
        get_mi_attempt_service,
        get_mi_progress_service,
    )
    
    app.dependency_overrides[get_mi_module_service] = override_get_mi_module_service
    app.dependency_overrides[get_mi_attempt_service] = override_get_mi_attempt_service
    app.dependency_overrides[get_mi_progress_service] = override_get_mi_progress_service
    
    # Mock authentication dependency
    from src.dependencies import get_current_user
    from src.auth.auth_dependencies import AuthenticatedUser
    
    def override_get_current_user():
        return AuthenticatedUser(
            user_id="test-user-001",
            email="test@example.com",
            role="FULL"
        )
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    # Also need to mock the module service used in review_attempt endpoint
    # which calls get_mi_module_service() directly instead of using Depends
    import src.dependencies
    original_get_mi_module_service = src.dependencies.get_mi_module_service
    src.dependencies._app_state.mi_module_service = mock_module_service
    
    app.include_router(mi_practice_router)
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client"""
    return TestClient(test_app)


# ============================================
# MODULE LISTING TESTS
# ============================================

class TestModuleListing:
    """Tests for module listing endpoints"""
    
    def test_list_modules_success(self, client):
        """Test successful module listing"""
        response = client.get("/api/mi-practice/modules")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["code"] == "mi-building-rapport-001"
        assert data[1]["code"] == "mi-explore-resistance-001"
    
    def test_list_modules_with_focus_area_filter(self, client, mock_module_service):
        """Test module listing with focus area filter"""
        response = client.get("/api/mi-practice/modules?focus_area=Building+Rapport")
        
        assert response.status_code == 200
        mock_module_service.list_modules.assert_called_once_with(
            content_type=None,
            focus_area="Building Rapport",
            difficulty=None,
            user_id=None,
        )
    
    def test_list_modules_with_difficulty_filter(self, client, mock_module_service):
        """Test module listing with difficulty filter"""
        response = client.get("/api/mi-practice/modules?difficulty=beginner")
        
        assert response.status_code == 200
        mock_module_service.list_modules.assert_called_once_with(
            content_type=None,
            focus_area=None,
            difficulty="beginner",
            user_id=None,
        )
    
    def test_list_modules_with_user_id(self, client, mock_module_service):
        """Test module listing with user_id for progress tracking"""
        response = client.get("/api/mi-practice/modules?user_id=test-user-001")
        
        assert response.status_code == 200
        mock_module_service.list_modules.assert_called_once_with(
            content_type=None,
            focus_area=None,
            difficulty=None,
            user_id="test-user-001",
        )


# ============================================
# MODULE RETRIEVAL TESTS
# ============================================

class TestModuleRetrieval:
    """Tests for module retrieval endpoints"""
    
    def test_get_module_success(self, client):
        """Test successful module retrieval"""
        response = client.get("/api/mi-practice/modules/mod-001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "mi-building-rapport-001"
        assert data["title"] == "Building Rapport with Alex"
        assert "dialogue_structure" in data
        assert "persona_config" in data
    
    def test_get_module_not_found(self, client, mock_module_service):
        """Test module retrieval when module doesn't exist"""
        async def mock_return_none(*args, **kwargs):
            return None
        mock_module_service.get_module.side_effect = mock_return_none
        
        response = client.get("/api/mi-practice/modules/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ============================================
# ATTEMPT LIFECYCLE TESTS
# ============================================

class TestAttemptLifecycle:
    """Tests for attempt start, choice making, and completion"""
    
    def test_start_attempt_success(self, client, mock_attempt_service):
        """Test starting a new attempt"""
        request_data = {
            "module_id": "mod-001",
            "user_id": "user-001",
        }
        
        response = client.post("/api/mi-practice/modules/mod-001/start", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["attempt_id"] == "attempt-001"
        assert data["module_code"] == "mi-building-rapport-001"
        assert "current_state" in data
        assert "choice_points" in data
        assert len(data["choice_points"]) == 2
    
    def test_start_attempt_no_user_id(self, client, mock_attempt_service):
        """Test starting attempt without user_id (uses anonymous)"""
        request_data = {"module_id": "mod-001"}
        
        response = client.post("/api/mi-practice/modules/mod-001/start", json=request_data)
        
        assert response.status_code == 200
        mock_attempt_service.start_attempt.assert_called_once_with("mod-001", "anonymous")
    
    def test_make_choice_success(self, client, mock_attempt_service):
        """Test making a choice in an attempt"""
        request_data = {"choice_point_id": "cp_1_open"}
        
        response = client.post("/api/mi-practice/attempts/attempt-001/choose", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["attempt_id"] == "attempt-001"
        assert data["turn_number"] == 1
        assert "feedback" in data
        assert "new_state" in data
        assert data["is_complete"] == True
    
    def test_make_choice_attempt_not_found(self, client, mock_attempt_service):
        """Test making choice when attempt doesn't exist"""
        async def mock_return_none(*args, **kwargs):
            return None
        mock_attempt_service.make_choice.side_effect = mock_return_none
        
        request_data = {"choice_point_id": "cp_1_open"}
        response = client.post("/api/mi-practice/attempts/nonexistent/choose", json=request_data)
        
        assert response.status_code == 404
    
    def test_get_attempt_state_success(self, client, mock_attempt_service):
        """Test getting attempt state"""
        async def mock_get_state(*args, **kwargs):
            return {
                "attempt_id": "attempt-001",
                "current_node_id": "node_1",
                "rapport_score": 0,
                "resistance_level": 5,
                "tone_position": 0.2,
                "choices_made": [],
            }
        mock_attempt_service.get_attempt_state = MagicMock(side_effect=mock_get_state)
        
        response = client.get("/api/mi-practice/attempts/attempt-001/state")
        
        assert response.status_code == 200
        data = response.json()
        assert data["attempt_id"] == "attempt-001"
        assert data["current_node_id"] == "node_1"
    
    def test_complete_attempt_success(self, client, mock_attempt_service, mock_progress_service):
        """Test completing an attempt"""
        # Fix: Make update_progress_after_attempt async
        async def mock_update_progress(*args, **kwargs):
            return True
        mock_progress_service.update_progress_after_attempt.side_effect = mock_update_progress
        
        response = client.post("/api/mi-practice/attempts/attempt-001/complete")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["attempt_id"] == "attempt-001"
        assert "final_scores" in data
        
        # Verify progress was updated
        mock_progress_service.update_progress_after_attempt.assert_called_once()


# ============================================
# PROGRESS TRACKING TESTS
# ============================================

class TestProgressTracking:
    """Tests for progress tracking endpoints"""
    
    def test_get_user_progress_success(self, client):
        """Test getting user progress"""
        response = client.get("/api/mi-practice/progress?user_id=test-user-001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["modules_completed"] == 5
        assert data["modules_attempted"] == 8
        assert "competency_scores" in data
        assert "techniques_practiced" in data
        assert "recent_attempts" in data
    
    def test_get_user_progress_missing_user_id(self, client):
        """Test getting progress without user_id"""
        response = client.get("/api/mi-practice/progress")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_competency_breakdown(self, client):
        """Test getting competency breakdown"""
        response = client.get("/api/mi-practice/progress/competencies?user_id=test-user-001")
        
        assert response.status_code == 200
        data = response.json()
        assert "A6" in data
        assert "B6" in data
        assert data["A6"]["current_score"] == 8.5
    
    def test_review_attempt(self, client):
        """Test reviewing a completed attempt"""
        response = client.get("/api/mi-practice/attempts/attempt-001/review")
        
        assert response.status_code == 200
        data = response.json()
        assert data["attempt_id"] == "attempt-001"
        assert "module" in data
        assert "final_scores" in data
        assert "path_review" in data
        assert "learning_notes" in data


# ============================================
# DISCOVERY & RECOMMENDATION TESTS
# ============================================

class TestDiscoveryEndpoints:
    """Tests for discovery and recommendation endpoints"""
    
    def test_get_focus_areas(self, client, mock_module_service):
        """Test getting focus areas"""
        async def mock_get_focus_areas():
            return [
                {"name": "Building Rapport", "module_count": 3},
                {"name": "Exploring Resistance", "module_count": 2},
            ]
        mock_module_service.get_focus_areas = MagicMock(side_effect=mock_get_focus_areas)
        
        response = client.get("/api/mi-practice/focus-areas")
        
        assert response.status_code == 200
        data = response.json()
        assert "focus_areas" in data
        assert len(data["focus_areas"]) == 2
    
    def test_get_difficulty_levels(self, client, mock_module_service):
        """Test getting difficulty levels"""
        async def mock_get_difficulty_levels():
            return [
                {"name": "beginner", "module_count": 5},
                {"name": "intermediate", "module_count": 3},
                {"name": "advanced", "module_count": 2},
            ]
        mock_module_service.get_difficulty_levels = MagicMock(side_effect=mock_get_difficulty_levels)
        
        response = client.get("/api/mi-practice/difficulty-levels")
        
        assert response.status_code == 200
        data = response.json()
        assert "difficulty_levels" in data
    
    def test_get_recommendations(self, client, mock_module_service):
        """Test getting module recommendations"""
        async def mock_get_recommended_modules(*args, **kwargs):
            return [
                {"id": "mod-003", "title": "Advanced Rapport Building", "reason": "Builds on your strengths"},
            ]
        mock_module_service.get_recommended_modules = MagicMock(side_effect=mock_get_recommended_modules)
        
        response = client.get("/api/mi-practice/recommendations?user_id=test-user-001")
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data


# ============================================
# HEALTH CHECK TESTS
# ============================================

class TestHealthCheck:
    """Tests for health check endpoint"""
    
    def test_health_check_healthy(self, client):
        """Test health check when system is healthy"""
        response = client.get("/api/mi-practice/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "mi-practice"
        assert "timestamp" in data


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestErrorHandling:
    """Tests for error handling"""
    
    def test_module_service_error(self, client, mock_module_service):
        """Test handling of module service errors"""
        mock_module_service.list_modules.side_effect = Exception("Database error")
        
        response = client.get("/api/mi-practice/modules")
        
        assert response.status_code == 500
        assert "database error" in response.json()["detail"].lower()
    
    def test_attempt_service_error(self, client, mock_attempt_service):
        """Test handling of attempt service errors"""
        mock_attempt_service.start_attempt.side_effect = Exception("Service unavailable")
        
        request_data = {"module_id": "mod-001"}
        response = client.post("/api/mi-practice/modules/mod-001/start", json=request_data)
        
        assert response.status_code == 500


# ============================================
# INTEGRATION WORKFLOW TESTS
# ============================================

class TestIntegrationWorkflow:
    """End-to-end workflow tests"""
    
    def test_complete_practice_workflow(self, client, mock_module_service, mock_attempt_service):
        """Test a complete practice session workflow"""
        # Step 1: List modules
        response = client.get("/api/mi-practice/modules")
        assert response.status_code == 200
        modules = response.json()
        assert len(modules) > 0
        
        # Step 2: Get module details
        module_id = modules[0]["id"]
        response = client.get(f"/api/mi-practice/modules/{module_id}")
        assert response.status_code == 200
        module = response.json()
        assert "dialogue_structure" in module
        
        # Step 3: Start attempt
        response = client.post(
            f"/api/mi-practice/modules/{module_id}/start",
            json={"module_id": module_id, "user_id": "test-user-001"}
        )
        assert response.status_code == 200
        attempt_data = response.json()
        attempt_id = attempt_data["attempt_id"]
        assert "choice_points" in attempt_data
        
        # Step 4: Make a choice
        choice_point_id = attempt_data["choice_points"][0]["id"]
        response = client.post(
            f"/api/mi-practice/attempts/{attempt_id}/choose",
            json={"choice_point_id": choice_point_id}
        )
        assert response.status_code == 200
        choice_data = response.json()
        assert "feedback" in choice_data
        
        # Step 5: Complete attempt
        response = client.post(f"/api/mi-practice/attempts/{attempt_id}/complete")
        assert response.status_code == 200
        complete_data = response.json()
        assert complete_data["success"] == True
        
        # Step 6: Review attempt
        response = client.get(f"/api/mi-practice/attempts/{attempt_id}/review")
        assert response.status_code == 200
        review_data = response.json()
        assert review_data["attempt_id"] == attempt_id
        
        # Step 7: Check progress
        response = client.get("/api/mi-practice/progress?user_id=test-user-001")
        assert response.status_code == 200
        progress_data = response.json()
        assert "modules_completed" in progress_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
