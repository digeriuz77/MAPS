#!/usr/bin/env python3
"""
Setup script to populate Supabase with proper persona templates
Creates personas that act as people receiving MI coaching, not providing it
"""

import asyncio
import uuid
import logging
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.dependencies import get_supabase_client
from src.config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Proper persona seeds - These are people who RECEIVE coaching, not provide it
PERSONA_TEMPLATES = [
    {
        "id": str(uuid.uuid4()),
        "persona_seed": "Mary - Stressed single parent juggling work and childcare. Recently received performance feedback and feels overwhelmed. Tends to get defensive when criticized but opens up when shown genuine empathy and understanding.",
        "status": "template",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "persona_seed": "Alex - Junior software developer struggling with impostor syndrome. Smart but doubts their abilities. Responds well to validation and becomes more confident when their expertise is acknowledged.",
        "status": "template",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "persona_seed": "Sam - Experienced manager dealing with team conflicts. Feels caught between upper management demands and team needs. Has strong opinions but will consider different perspectives when approached thoughtfully.",
        "status": "template",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "persona_seed": "Jordan - Healthcare worker experiencing burnout. Dedicated to patients but struggling with work-life balance. Initially resistant to change but opens up about deeper concerns when trust is established.",
        "status": "template",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "persona_seed": "Casey - Recent college graduate unsure about career direction. Anxious about making the 'right' choice. Becomes more reflective when asked open questions rather than given direct advice.",
        "status": "template",
        "created_at": datetime.utcnow().isoformat()
    }
]

async def setup_persona_templates():
    """Create persona templates in Supabase conversations table"""
    try:
        settings = get_settings()
        supabase = get_supabase_client()

        logger.info("Setting up persona templates in Supabase...")

        # Clear any existing templates first
        logger.info("Clearing existing persona templates...")
        delete_response = supabase.table('conversations').delete().eq('status', 'template').execute()
        logger.info(f"Deleted {len(delete_response.data) if delete_response.data else 0} existing templates")

        # Insert new persona templates
        logger.info("Inserting new persona templates...")
        insert_response = supabase.table('conversations').insert(PERSONA_TEMPLATES).execute()

        if insert_response.data:
            logger.info(f"Successfully created {len(insert_response.data)} persona templates:")
            for template in insert_response.data:
                persona_name = template['persona_seed'].split(' - ')[0]
                logger.info(f"  - {persona_name}")
        else:
            logger.error("Failed to insert persona templates")
            return False

        # Verify the templates were created
        logger.info("Verifying persona templates...")
        verify_response = supabase.table('conversations').select('id, persona_seed').eq('status', 'template').execute()

        if verify_response.data:
            logger.info(f"Verification successful: {len(verify_response.data)} templates found")
            return True
        else:
            logger.error("Verification failed: No templates found after insertion")
            return False

    except Exception as e:
        logger.error(f"Failed to setup persona templates: {e}")
        return False

async def test_api_endpoints():
    """Test that the clean API endpoints work with new personas"""
    try:
        logger.info("Testing API endpoints...")

        # This would require making HTTP requests to the running server
        # For now, just log that manual testing is needed
        logger.info("✓ Persona templates created successfully")
        logger.info("➤ Manual test needed:")
        logger.info("  1. Start the server: python -m uvicorn src.main:app --host 0.0.0.0 --port 8001")
        logger.info("  2. Test personas endpoint: GET http://localhost:8001/api/chat/personas")
        logger.info("  3. Test conversation start: POST http://localhost:8001/api/chat/start")

        return True

    except Exception as e:
        logger.error(f"API endpoint test preparation failed: {e}")
        return False

async def main():
    """Main setup function"""
    logger.info("=== Persona Setup Script ===")

    # Step 1: Setup persona templates
    if not await setup_persona_templates():
        logger.error("Failed to setup persona templates")
        return False

    # Step 2: Test API endpoints
    if not await test_api_endpoints():
        logger.error("API endpoint test preparation failed")
        return False

    logger.info("=== Setup Complete ===")
    logger.info("Personas are now ready for use with the clean API system")
    logger.info("Next steps:")
    logger.info("1. Update HTML frontend to use /api/chat/* endpoints")
    logger.info("2. Test conversation flow with real MI analysis")

    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)