"""
Comprehensive Endpoint Testing Script
Tests all API endpoints with both FULL and CONTROL user authentication
"""
import asyncio
import httpx
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  # Change for production
FULL_USER_TOKEN = os.getenv("FULL_USER_TOKEN", "")  # JWT token for FULL access user
CONTROL_USER_TOKEN = os.getenv("CONTROL_USER_TOKEN", "")  # JWT token for CONTROL access user

# Test results storage
test_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "tests": []
}

class EndpointTest:
    def __init__(self, name: str, method: str, path: str, auth_required: bool = False, 
                 full_only: bool = False, payload: Optional[Dict] = None, 
                 query_params: Optional[Dict] = None):
        self.name = name
        self.method = method.upper()
        self.path = path
        self.auth_required = auth_required
        self.full_only = full_only
        self.payload = payload
        self.query_params = query_params
    
    async def run(self, client: httpx.AsyncClient, token: Optional[str] = None, 
                  role: str = "NONE") -> Dict:
        """Execute the test"""
        url = f"{BASE_URL}{self.path}"
        headers = {}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if self.method == "GET":
                response = await client.get(url, headers=headers, params=self.query_params, timeout=30.0)
            elif self.method == "POST":
                response = await client.post(url, headers=headers, json=self.payload, timeout=30.0)
            elif self.method == "DELETE":
                response = await client.delete(url, headers=headers, timeout=30.0)
            else:
                return {
                    "status": "FAILED",
                    "error": f"Unsupported method: {self.method}",
                    "status_code": 0
                }
            
            # Analyze response
            status_code = response.status_code
            
            # Expected behavior
            if not self.auth_required:
                # Public endpoint - should work
                expected = status_code in [200, 201]
            elif self.full_only and role == "CONTROL":
                # FULL-only endpoint accessed by CONTROL user - should be 403
                expected = status_code == 403
            elif self.auth_required and not token:
                # Auth required but no token - should be 401
                expected = status_code == 401
            elif self.auth_required and token:
                # Auth required with token - should work (200-299)
                expected = 200 <= status_code < 300
            else:
                expected = 200 <= status_code < 300
            
            result = {
                "status": "PASSED" if expected else "FAILED",
                "status_code": status_code,
                "role": role,
                "expected": expected,
                "response_time": response.elapsed.total_seconds(),
                "response_preview": None,
                "error": None
            }
            
            # Try to parse response
            try:
                result["response_preview"] = response.json()
            except:
                result["response_preview"] = response.text[:200] if response.text else None
            
            return result
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "status_code": 0,
                "role": role
            }

async def run_tests():
    """Run all endpoint tests"""
    
    print("=" * 80)
    print("COMPREHENSIVE ENDPOINT TESTING")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"FULL Token: {'✓ Configured' if FULL_USER_TOKEN else '✗ Missing'}")
    print(f"CONTROL Token: {'✓ Configured' if CONTROL_USER_TOKEN else '✗ Missing'}")
    print("=" * 80)
    print()
    
    # Define all endpoint tests
    tests = [
        # ===== CHAT ENDPOINTS (enhanced_chat.py) =====
        EndpointTest("Get Enhanced Personas", "GET", "/api/chat/personas", auth_required=False),
        EndpointTest("Start Enhanced Conversation - FULL", "POST", "/api/chat/start", 
                     auth_required=True, full_only=False,
                     payload={"persona_id": "petra"}),
        EndpointTest("Start Enhanced Conversation - CONTROL", "POST", "/api/chat/start", 
                     auth_required=True, full_only=False,
                     payload={"persona_id": "petra"}),
        
        # Note: /api/chat/send requires valid conversation_id, tested separately
        
        # ===== ANALYSIS ENDPOINTS (analysis.py) =====
        EndpointTest("Submit Analysis Text - FULL", "POST", "/api/v1/analysis/text",
                     auth_required=True, full_only=True,
                     payload={
                         "transcript": "Coach: How are you feeling today?\nPerson: I'm doing okay.",
                         "context": {},
                         "speaker_hints": {}
                     }),
        EndpointTest("Submit Analysis Text - CONTROL", "POST", "/api/v1/analysis/text",
                     auth_required=True, full_only=True,
                     payload={
                         "transcript": "Coach: How are you feeling today?\nPerson: I'm doing okay.",
                         "context": {},
                         "speaker_hints": {}
                     }),
        EndpointTest("Clear Analysis Cache", "DELETE", "/api/v1/analysis/cache",
                     auth_required=False),
        
        # ===== REFLECTION ENDPOINTS (reflection.py) =====
        EndpointTest("Reflection Health Check", "GET", "/api/reflection/health", auth_required=False),
        EndpointTest("Generate Reflection Summary - FULL", "POST", "/api/reflection/generate-summary",
                     auth_required=True, full_only=True,
                     payload={
                         "question1_response": "I felt I listened well and used open questions.",
                         "question2_response": "I struggled with avoiding giving advice.",
                         "question3_response": "Next time I'll focus more on reflections.",
                         "session_id": "test-session-123",
                         "persona_practiced": "Test Persona"
                     }),
        EndpointTest("Generate Reflection Summary - CONTROL", "POST", "/api/reflection/generate-summary",
                     auth_required=True, full_only=True,
                     payload={
                         "question1_response": "I felt I listened well and used open questions.",
                         "question2_response": "I struggled with avoiding giving advice.",
                         "question3_response": "Next time I'll focus more on reflections.",
                         "session_id": "test-session-123",
                         "persona_practiced": "Test Persona"
                     }),
        
        # ===== FEEDBACK ENDPOINTS (feedback.py) =====
        EndpointTest("Submit Feedback - FULL", "POST", "/api/feedback/submit",
                     auth_required=True, full_only=True,
                     payload={
                         "session_id": "test-session-123",
                         "conversation_id": None,
                         "persona_practiced": "Test Persona",
                         "helpfulness_score": 8,
                         "what_was_helpful": "The realistic responses",
                         "improvement_suggestions": "More personas"
                     }),
        EndpointTest("Submit Feedback - CONTROL", "POST", "/api/feedback/submit",
                     auth_required=True, full_only=True,
                     payload={
                         "session_id": "test-session-123",
                         "conversation_id": None,
                         "persona_practiced": "Test Persona",
                         "helpfulness_score": 8,
                         "what_was_helpful": "The realistic responses",
                         "improvement_suggestions": "More personas"
                     }),
        EndpointTest("Get Feedback Stats", "GET", "/api/feedback/stats",
                     auth_required=False),
        
        # ===== METRICS ENDPOINTS (metrics.py) =====
        EndpointTest("Get Metrics", "GET", "/api/metrics", auth_required=False),
        
        # ===== WEB API ENDPOINTS (web_api.py) =====
        EndpointTest("List Web Personas", "GET", "/api/web/personas", auth_required=False),
        EndpointTest("Get Dialogue Scenarios", "GET", "/api/web/v1/dialogue/scenarios", auth_required=False),
        
        # ===== MAPS ANALYSIS ENDPOINTS (maps_analysis.py) =====
        EndpointTest("MAPS Analyze Transcript - FULL", "POST", "/api/v1/maps/analyze/transcript",
                     auth_required=True, full_only=True,
                     payload={
                         "transcript": "Manager: How are you feeling about the project?\nEmployee: I'm a bit worried about the deadline.",
                         "context": {},
                         "manager_name": "Manager",
                         "persona_name": "Employee"
                     }),
    ]
    
    async with httpx.AsyncClient() as client:
        print(f"Running {len(tests)} endpoint tests...\n")
        
        for test in tests:
            test_results["total_tests"] += 1
            
            print(f"Test {test_results['total_tests']}: {test.name}")
            print(f"  Method: {test.method} {test.path}")
            print(f"  Auth Required: {test.auth_required}, FULL Only: {test.full_only}")
            
            # Determine which token to use
            if "FULL" in test.name:
                token = FULL_USER_TOKEN
                role = "FULL"
            elif "CONTROL" in test.name:
                token = CONTROL_USER_TOKEN
                role = "CONTROL"
            else:
                token = None if not test.auth_required else FULL_USER_TOKEN
                role = "FULL" if token == FULL_USER_TOKEN else "CONTROL" if token == CONTROL_USER_TOKEN else "NONE"
            
            result = await test.run(client, token, role)
            
            # Store result
            test_record = {
                "name": test.name,
                "method": test.method,
                "path": test.path,
                "timestamp": datetime.now().isoformat(),
                **result
            }
            test_results["tests"].append(test_record)
            
            # Update counters
            if result["status"] == "PASSED":
                test_results["passed"] += 1
                print(f"  Result: ✓ PASSED (Status: {result['status_code']})")
            else:
                test_results["failed"] += 1
                print(f"  Result: ✗ FAILED (Status: {result.get('status_code', 'N/A')})")
                if result.get("error"):
                    print(f"  Error: {result['error']}")
            
            print()
    
    # Generate summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed']} ({test_results['passed']/test_results['total_tests']*100:.1f}%)")
    print(f"Failed: {test_results['failed']} ({test_results['failed']/test_results['total_tests']*100:.1f}%)")
    print()
    
    # Group failures by endpoint
    if test_results['failed'] > 0:
        print("FAILED TESTS:")
        print("-" * 80)
        for test in test_results["tests"]:
            if test["status"] == "FAILED":
                print(f"  • {test['name']}")
                print(f"    {test['method']} {test['path']}")
                print(f"    Status: {test.get('status_code', 'N/A')}, Role: {test.get('role', 'N/A')}")
                if test.get("error"):
                    print(f"    Error: {test['error']}")
                print()
    
    # Save detailed results to file
    output_file = f"endpoint_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")
    print("=" * 80)
    
    return test_results

def main():
    """Main entry point"""
    if not FULL_USER_TOKEN or not CONTROL_USER_TOKEN:
        print("⚠️  WARNING: Authentication tokens not configured!")
        print("Set FULL_USER_TOKEN and CONTROL_USER_TOKEN environment variables")
        print("Tests will run but authentication-required endpoints will fail")
        print()
        
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(1)
    
    # Run tests
    results = asyncio.run(run_tests())
    
    # Exit with appropriate code
    sys.exit(0 if results["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
