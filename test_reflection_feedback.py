"""
Test script for Reflection Summary and User Feedback endpoints
"""
import asyncio
import sys
from datetime import datetime
import uuid

# Add src to path
sys.path.insert(0, "C:\\builds\\character\\character-ai-chat")

from src.dependencies import get_supabase_client
from src.services.llm_service import LLMService


async def test_reflection_summary():
    """Test reflection summary generation"""
    print("\n" + "="*60)
    print("TESTING REFLECTION SUMMARY GENERATION")
    print("="*60)
    
    try:
        # Initialize services
        supabase = get_supabase_client()
        llm_service = LLMService()
        
        # Test reflection responses
        question1_response = "I felt confident building rapport and using open-ended questions."
        question2_response = "I struggled with knowing when to move from reflections to asking deeper questions."
        question3_response = "I would practice more affirmations and focus on the client's strengths."
        
        print("\nTest Input:")
        print(f"Q1 (What went well): {question1_response}")
        print(f"Q2 (Struggles): {question2_response}")
        print(f"Q3 (Future improvements): {question3_response}")
        
        # Get reflection prompt from database
        print("\n📥 Fetching reflection prompt from database...")
        prompt_result = supabase.table('system_prompts')\
            .select('*')\
            .eq('prompt_key', 'reflection_summary')\
            .maybe_single()\
            .execute()
        
        if prompt_result.data and prompt_result.data.get('prompt_text'):
            base_prompt = prompt_result.data['prompt_text']
            model_to_use = prompt_result.data.get('model_recommended', 'gpt-4o-mini')
            temperature = prompt_result.data.get('temperature', 0.7)
            max_tokens = prompt_result.data.get('max_tokens', 600)
            print(f"✓ Using prompt from database")
            print(f"  Model: {model_to_use}")
            print(f"  Temperature: {temperature}")
            print(f"  Max tokens: {max_tokens}")
        else:
            print("⚠ Prompt not found in database, using fallback")
            base_prompt = """Based on the following reflection responses, create a concise, cohesive summary (2-3 paragraphs) that synthesizes the practitioner's insights:

What went well: {question1}

Struggles: {question2}

Future improvements: {question3}

Provide an encouraging, professional summary that highlights key insights and growth opportunities."""
            model_to_use = "gpt-4o-mini"
            temperature = 0.7
            max_tokens = 600
        
        # Format prompt
        formatted_prompt = base_prompt.format(
            question1=question1_response,
            question2=question2_response,
            question3=question3_response
        )
        
        # Generate summary
        print("\n🤖 Generating summary with LLM...")
        summary = await llm_service.generate_response(
            prompt=formatted_prompt,
            system_prompt="You are an expert person-centred coach providing thoughtful, encouraging reflection summaries for motivational interviewing practice sessions.",
            model=model_to_use,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if summary and summary.strip():
            print("\n✅ SUCCESS - Summary generated:")
            print("-" * 60)
            print(summary.strip())
            print("-" * 60)
            
            # Store in database
            print("\n💾 Storing reflection in database...")
            reflection_data = {
                'id': str(uuid.uuid4()),  # Generate proper UUID for id field
                'user_id': '00000000-0000-0000-0000-000000000001',
                'session_date': datetime.utcnow().date().isoformat(),
                'question1': question1_response,
                'question2': question2_response,
                'question3': question3_response,
                'summary': summary.strip(),
                'metadata': {
                    'test_session': True,
                    'session_type': 'test_reflection'
                }
            }
            
            result = supabase.table('reflection_sessions').insert(reflection_data).execute()
            
            if result.data:
                print(f"✓ Stored in database with ID: {result.data[0]['id']}")
                return True
            else:
                print("⚠ Failed to store in database")
                return False
        else:
            print("\n❌ FAILED - Summary was empty")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_user_feedback():
    """Test user feedback submission"""
    print("\n" + "="*60)
    print("TESTING USER FEEDBACK SUBMISSION")
    print("="*60)
    
    try:
        # Initialize Supabase
        supabase = get_supabase_client()
        
        # Test feedback data
        feedback_data = {
            "id": str(uuid.uuid4()),  # Generate proper UUID for id field
            "session_id": "test-session-123",
            "conversation_id": None,
            "persona_practiced": "Petra Jones",
            "helpfulness_score": 8,
            "what_was_helpful": "The persona was very realistic and challenged me to practice active listening.",
            "improvement_suggestions": "Maybe add more difficult scenarios.",
            "user_email": "test@example.com",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {"test": True}
        }
        
        print("\nTest Feedback Data:")
        print(f"  Session ID: {feedback_data['session_id']}")
        print(f"  Persona: {feedback_data['persona_practiced']}")
        print(f"  Score: {feedback_data['helpfulness_score']}/10")
        print(f"  Helpful: {feedback_data['what_was_helpful']}")
        print(f"  Suggestions: {feedback_data['improvement_suggestions']}")
        
        # Submit to database
        print("\n💾 Storing feedback in database...")
        result = supabase.table('user_feedback').insert(feedback_data).execute()
        
        if result.data:
            print(f"✅ SUCCESS - Feedback stored with ID: {result.data[0]['id']}")
            
            # Test retrieval
            print("\n📊 Testing feedback stats retrieval...")
            stats_result = supabase.table('user_feedback').select('*').execute()
            
            if stats_result.data:
                scores = [f['helpfulness_score'] for f in stats_result.data]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                print(f"✓ Total feedback entries: {len(stats_result.data)}")
                print(f"✓ Average score: {avg_score:.2f}/10")
                return True
            else:
                print("⚠ No feedback data found")
                return False
        else:
            print("❌ FAILED - Could not store feedback")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("REFLECTION & FEEDBACK SYSTEM TEST")
    print("="*60)
    print(f"Test started at: {datetime.utcnow().isoformat()}")
    
    # Test 1: Reflection Summary
    summary_result = await test_reflection_summary()
    
    # Test 2: User Feedback
    feedback_result = await test_user_feedback()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Reflection Summary: {'✅ PASSED' if summary_result else '❌ FAILED'}")
    print(f"User Feedback: {'✅ PASSED' if feedback_result else '❌ FAILED'}")
    print("="*60)
    
    if summary_result and feedback_result:
        print("\n🎉 All tests PASSED!")
        return 0
    else:
        print("\n⚠️  Some tests FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
