"""
Smart Memory Management System for Persona Conversations
Prevents memory overload while maintaining important context continuity
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MemoryManagementConfig:
    """Configuration for memory management thresholds"""
    max_total_memories: int = 12  # Hard limit per conversation (reduced from 20)
    max_session_memories: int = 8  # Max memories to use in any single session
    core_memory_threshold: float = 8.5  # Memories above this never get archived
    session_memory_decay_days: int = 7  # Regular memories fade after this time
    core_memory_decay_days: int = 30  # Core memories fade after this time
    baseline_reset_threshold: int = 15  # Reset when memories exceed this count (reduced from 25)

class SmartMemoryManager:
    """
    Manages persona memory lifecycle to prevent overload while maintaining continuity
    
    Features:
    - Memory archival (moves old memories to separate table)
    - Importance-based retention (keeps high-impact memories)
    - Session-specific memory limits
    - Automatic baseline reset when needed
    """
    
    def __init__(self, supabase_client, config: MemoryManagementConfig = None):
        self.supabase = supabase_client
        self.config = config or MemoryManagementConfig()
    
    async def manage_conversation_memories(self, conversation_id: str, persona_name: str = "Mary") -> Dict:
        """
        Comprehensive memory management for a conversation
        Returns summary of actions taken
        """
        actions_taken = {
            "total_memories_before": 0,
            "total_memories_after": 0,
            "memories_archived": 0,
            "memories_retained": 0,
            "baseline_reset_triggered": False,
            "memory_quality_distribution": {},
            "recommended_action": ""
        }
        
        try:
            # Step 1: Get current memory count and distribution
            current_memories = await self._get_memory_distribution(conversation_id, persona_name)
            actions_taken["total_memories_before"] = len(current_memories)

            # Step 2: Separate static (persona background) from dynamic (conversation) memories
            # Only count DYNAMIC memories for reset/archival thresholds
            # Static persona memories are permanent and shouldn't be archived
            dynamic_memories = []
            static_memories = []

            for m in current_memories:
                metadata = m.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        import json
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}

                if metadata.get('type') == 'dynamic_interaction':
                    dynamic_memories.append(m)
                else:
                    static_memories.append(m)

            logger.info(f"Memory management: {len(dynamic_memories)} dynamic, {len(static_memories)} static (total: {len(current_memories)})")

            # Step 3: Check if baseline reset is needed (ONLY for dynamic memories)
            if len(dynamic_memories) >= self.config.baseline_reset_threshold:
                await self._perform_baseline_reset(conversation_id, persona_name, dynamic_memories)
                actions_taken["baseline_reset_triggered"] = True
                actions_taken["recommended_action"] = "Full baseline reset performed"
                return actions_taken

            # Step 4: Normal memory management (ONLY for dynamic memories)
            if len(dynamic_memories) > self.config.max_total_memories:
                archived_count = await self._archive_old_memories(conversation_id, persona_name, dynamic_memories)
                actions_taken["memories_archived"] = archived_count
                actions_taken["recommended_action"] = f"Archived {archived_count} old memories"
            
            # Step 4: Get final state
            final_memories = await self._get_memory_distribution(conversation_id, persona_name)
            actions_taken["total_memories_after"] = len(final_memories)
            actions_taken["memories_retained"] = len(final_memories)
            
            # Step 5: Quality analysis
            actions_taken["memory_quality_distribution"] = self._analyze_memory_quality(final_memories)
            
            if not actions_taken["recommended_action"]:
                actions_taken["recommended_action"] = "Memory levels healthy, no action needed"
            
            logger.info(f"Memory management complete: {actions_taken['total_memories_before']} -> {actions_taken['total_memories_after']} memories")
            
        except Exception as e:
            logger.error(f"Memory management failed: {e}")
            actions_taken["error"] = str(e)
        
        return actions_taken
    
    async def get_session_baseline_memories(
        self,
        conversation_id: str,
        persona_name: str = "Mary",
        conversation_state: Optional[object] = None,
        current_topics: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get curated memories using TRUST-BASED PROGRESSIVE REVELATION

        Memory selection based on:
        1. Trust level & conversation stage (what Mary is willing to share)
        2. Topic relevance (match current conversation topics)
        3. Relationship context (what Mary has already shared with THIS user)

        OPTIMIZATION: Filtering done at database level via WHERE clauses
        """
        try:
            # Extract trust level and stage from conversation_state
            trust_level = 5.0  # Default neutral
            stage = "building_rapport"
            key_topics = current_topics or []

            if conversation_state:
                trust_level = getattr(conversation_state, 'trust_level', 5.0)
                stage = getattr(conversation_state, 'stage', 'building_rapport')
                key_topics = getattr(conversation_state, 'key_topics', [])

            # PROGRESSIVE REVELATION: Define what Mary is willing to share at each trust level
            # Trust must be EARNED - starts defensive with strangers
            if stage == "defensive" or trust_level < 3.0:
                max_importance = 3.0
                allowed_types = ['neutral_fact', 'professional_role']  # Only job title, basic facts
                logger.info(f"🛡️ DEFENSIVE (trust={trust_level:.1f}): Minimal sharing, guarded (importance ≤3.0)")
            elif stage == "cautious" or trust_level < 4.5:
                max_importance = 5.0
                allowed_types = ['work_challenge', 'personality_trait', 'professional_role']
                logger.info(f"⚠️ CAUTIOUS (trust={trust_level:.1f}): Surface-level only (importance ≤5.0)")
            elif stage == "building_rapport" or trust_level < 6.5:
                max_importance = 7.0
                allowed_types = ['work_challenge', 'personality_trait', 'professional_achievement']
                logger.info(f"🔒 BUILDING RAPPORT (trust={trust_level:.1f}): Testing trust, work challenges (importance ≤7.0)")
            elif stage == "opening_up" or trust_level < 8.0:
                max_importance = 8.5
                allowed_types = ['work_challenge', 'family_concern', 'coping_mechanism', 'personality_trait', 'professional_achievement']
                logger.info(f"🔓 OPENING UP (trust={trust_level:.1f}): Sharing family concerns, vulnerability (importance ≤8.5)")
            else:  # full_trust or trust >= 8.0
                max_importance = 10.0
                allowed_types = None  # All types allowed
                logger.info(f"❤️ FULL TRUST (trust={trust_level:.1f}): Complete vulnerability, ready for partnership (all memories)")

            # Get filtered memories from database (not Python)
            static_memories = await self._get_filtered_static_memories(
                conversation_id, persona_name, max_importance, allowed_types
            )
            dynamic_memories = await self._get_dynamic_memories(conversation_id)

            # TOPIC MATCHING: Boost memories that match current conversation topics
            def calculate_relevance_score(memory):
                """Calculate relevance based on importance + topic match"""
                importance = memory.get('importance_score', 0)
                metadata = memory.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        import json
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}

                category = metadata.get('category', '')
                memory_type = metadata.get('type', '')
                memory_text = memory.get('memory_text') or ''
                memory_text_lower = memory_text.lower() if memory_text else ''

                # Base score is importance
                score = importance

                # Boost if matches current topics
                for topic in key_topics:
                    if topic in category or topic in memory_type or topic in memory_text_lower:
                        score += 2.0  # Significant boost for topic match
                        logger.info(f"   📌 Topic match '{topic}': {memory_text[:80]}... (boosted +2.0)")

                return score

            # Sort by relevance (importance + topic matching)
            static_memories = sorted(static_memories, key=calculate_relevance_score, reverse=True)
            dynamic_memories = sorted(dynamic_memories, key=lambda x: x.get('importance_score', 0), reverse=True)

            # Build session memory set
            session_memories = []

            # Priority 1: Dynamic memories (relationship state) - max 3
            session_memories.extend(dynamic_memories[:3])

            # Priority 2: Static memories (background to share) - fill remaining slots
            remaining_slots = max(0, self.config.max_session_memories - len(session_memories))
            session_memories.extend(static_memories[:remaining_slots])

            logger.info(f"📝 Memory selection complete:")
            logger.info(f"   Stage: {stage}, Trust: {trust_level:.1f}")
            logger.info(f"   Dynamic memories: {len(dynamic_memories[:3])}")
            logger.info(f"   Static memories: {len(static_memories[:remaining_slots])} (filtered from {len(static_memories)} available)")
            logger.info(f"   Topics in focus: {key_topics}")
            logger.info(f"   Total memories returned: {len(session_memories)}")

            return session_memories[:self.config.max_session_memories]

        except Exception as e:
            logger.error(f"Failed to get session baseline: {e}")
            return []
    
    async def _get_memory_distribution(self, conversation_id: str, persona_name: str) -> List[Dict]:
        """Get all memories for a conversation with metadata - combines static + dynamic + UNIVERSAL memories"""
        try:
            # Get dynamic memories from conversation_memories table
            dynamic_result = self.supabase.table('conversation_memories').select('*').eq(
                'session_id', conversation_id
            ).order('created_at', desc=True).execute()
            
            dynamic_memories = []
            if dynamic_result.data:
                for memory in dynamic_result.data:
                    # Convert conversation_memories format to standard format
                    dynamic_memories.append({
                        'id': memory.get('id'),
                        'conversation_id': conversation_id,
                        'persona_name': persona_name,
                        'memory_text': memory.get('key_insights', ''),
                        'importance_score': memory.get('importance_score', 6.0),
                        'created_at': memory.get('created_at'),
                        'metadata': {
                            'type': 'dynamic_interaction',
                            'source_table': 'conversation_memories'
                            # conversation_memories table doesn't store detailed metadata
                        }
                    })
            
            # Get conversation-specific static memories from persona_memories table
            conversation_static_result = self.supabase.table('persona_memories').select('*').eq(
                'conversation_id', conversation_id
            ).eq('persona_name', persona_name).order('created_at', desc=True).execute()
            
            # CRITICAL FIX: Get UNIVERSAL static memories (available to all conversations)
            universal_static_result = self.supabase.table('persona_memories').select('*').eq(
                'conversation_id', '00000000-0000-0000-0000-000000000000'
            ).eq('persona_name', persona_name).order('importance_score', desc=True).execute()
            
            static_memories = []
            
            # Process conversation-specific static memories
            if conversation_static_result.data:
                for memory in conversation_static_result.data:
                    metadata = memory.get('metadata', {})
                    if not metadata.get('type'):
                        metadata['type'] = 'static_conversation'
                    metadata['source_table'] = 'persona_memories'
                    metadata['scope'] = 'conversation_specific'
                    
                    static_memories.append({
                        **memory,
                        'metadata': metadata
                    })
            
            # ENHANCEMENT: Process UNIVERSAL static memories (the rich background context)
            if universal_static_result.data:
                for memory in universal_static_result.data:
                    metadata = memory.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}

                    if not metadata.get('type'):
                        metadata['type'] = 'static_universal'
                    metadata['source_table'] = 'persona_memories'
                    metadata['scope'] = 'universal'

                    # Keep original importance scores - they're already properly categorized in migration 015
                    # Static memories (8-9) provide rich life stories Mary can share
                    # Dynamic memories (6-10) show relationship state with THIS person
                    # Both are important but serve different purposes

                    static_memories.append({
                        **memory,
                        'metadata': metadata
                    })
            
            # Combine and return all memories
            all_memories = dynamic_memories + static_memories
            
            logger.info(f"Memory distribution: {len(dynamic_memories)} dynamic + {len(static_memories)} static (universal: {len(universal_static_result.data) if universal_static_result.data else 0}) = {len(all_memories)} total")
            
            return all_memories
            
        except Exception as e:
            logger.error(f"Failed to get memory distribution: {e}")
            return []
    
    async def _archive_old_memories(self, conversation_id: str, persona_name: str, memories: List[Dict]) -> int:
        """Archive old, low-importance memories to separate table"""
        if len(memories) <= self.config.max_total_memories:
            return 0
        
        try:
            # Sort by importance and age to identify candidates for archival
            archival_candidates = []
            cutoff_date = datetime.now() - timedelta(days=self.config.session_memory_decay_days)
            
            for memory in memories:
                importance = memory.get('importance_score', 0)
                created_at_str = memory.get('created_at', datetime.now().isoformat())
                # Handle timezone-aware datetime parsing
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    # Convert to naive datetime for comparison
                    if created_at.tzinfo is not None:
                        created_at = created_at.replace(tzinfo=None)
                except (ValueError, AttributeError):
                    created_at = datetime.now()
                memory_type = memory.get('metadata', {}).get('type', 'static')
                
                # Don't archive core memories or very recent dynamic memories
                if (importance < self.config.core_memory_threshold and 
                    created_at < cutoff_date and 
                    memory_type != 'dynamic_interaction'):
                    archival_candidates.append(memory)
            
            # Archive excess memories
            memories_to_archive = len(memories) - self.config.max_total_memories
            to_archive = sorted(archival_candidates, key=lambda x: x['importance_score'])[:memories_to_archive]
            
            if to_archive:
                # Move to archived_memories table
                archive_data = []
                memory_ids_to_delete = []
                
                for memory in to_archive:
                    archive_record = {
                        **memory,
                        'archived_at': datetime.now().isoformat(),
                        'archive_reason': 'memory_management_cleanup'
                    }
                    archive_data.append(archive_record)
                    memory_ids_to_delete.append(memory['id'])
                
                # Insert into archive table (create if needed)
                await self._ensure_archive_table_exists()
                self.supabase.table('archived_persona_memories').insert(archive_data).execute()
                
                # Delete from active memories
                for memory_id in memory_ids_to_delete:
                    self.supabase.table('persona_memories').delete().eq('id', memory_id).execute()
                
                logger.info(f"Archived {len(to_archive)} memories to maintain memory limits")
                return len(to_archive)
            
        except Exception as e:
            logger.error(f"Failed to archive memories: {e}")
        
        return 0
    
    async def _perform_baseline_reset(self, conversation_id: str, persona_name: str, memories: List[Dict]):
        """Perform a baseline reset - keep only the most essential memories + create session summary"""
        try:
            # ENHANCEMENT: Create session summary before archiving
            session_summary = await self._create_session_summary(memories)
            
            # Keep only the highest importance memories (top 5) + session summary
            essential_memories = sorted(memories, key=lambda x: x['importance_score'], reverse=True)[:5]
            
            # Archive all other memories
            await self._ensure_archive_table_exists()
            
            memories_to_archive = [m for m in memories if m not in essential_memories]
            
            if memories_to_archive:
                archive_data = []
                memory_ids_to_delete = []
                
                for memory in memories_to_archive:
                    archive_record = {
                        **memory,
                        'archived_at': datetime.now().isoformat(),
                        'archive_reason': 'baseline_reset'
                    }
                    archive_data.append(archive_record)
                    memory_ids_to_delete.append(memory['id'])
                
                # Archive and delete
                self.supabase.table('archived_persona_memories').insert(archive_data).execute()
                
                for memory_id in memory_ids_to_delete:
                    # Delete from appropriate table based on memory source
                    metadata = next((m.get('metadata', {}) for m in memories if m['id'] == memory_id), {})
                    source_table = metadata.get('source_table', 'persona_memories')
                    
                    if source_table == 'conversation_memories':
                        self.supabase.table('conversation_memories').delete().eq('id', memory_id).execute()
                    else:
                        self.supabase.table('persona_memories').delete().eq('id', memory_id).execute()
                
                # Insert session summary as a new memory
                if session_summary:
                    summary_data = {
                        'session_id': conversation_id,
                        'key_insights': session_summary['memory_text'],
                        'importance_score': session_summary['importance_score'],
                        'created_at': datetime.now().isoformat()
                    }
                    self.supabase.table('conversation_memories').insert(summary_data).execute()
                    logger.info(f"📝 SESSION SUMMARY: Created summary memory with importance {session_summary['importance_score']}")
                
                logger.info(f"Baseline reset: Archived {len(memories_to_archive)} memories, kept {len(essential_memories)} essential memories + summary")
        
        except Exception as e:
            logger.error(f"Baseline reset failed: {e}")
    
    async def _get_filtered_static_memories(
        self,
        conversation_id: str,
        persona_name: str,
        max_importance: float,
        allowed_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get static memories filtered at DATABASE level by importance and type
        Much more efficient than pulling all memories and filtering in Python
        """
        try:
            # Build query for universal static memories
            query = self.supabase.table('persona_memories').select('*').eq(
                'conversation_id', '00000000-0000-0000-0000-000000000000'
            ).eq('persona_name', persona_name).lte('importance_score', max_importance)

            # Execute query
            result = query.order('importance_score', desc=True).execute()

            memories = []
            if result.data:
                for memory in result.data:
                    metadata = memory.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            import json
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}

                    # Filter by type if specified (can't do this in Supabase JSONB query easily)
                    memory_type = metadata.get('type', 'static')
                    if allowed_types is None or memory_type in allowed_types:
                        # Normalize metadata
                        metadata['source_table'] = 'persona_memories'
                        metadata['scope'] = 'universal'
                        memories.append({
                            **memory,
                            'metadata': metadata
                        })

            logger.info(f"   📊 Database filtered: {len(memories)} static memories (importance ≤{max_importance})")
            return memories

        except Exception as e:
            logger.error(f"Failed to get filtered static memories: {e}")
            return []

    async def _get_dynamic_memories(self, conversation_id: str) -> List[Dict]:
        """Get dynamic conversation memories from conversation_memories table"""
        try:
            result = self.supabase.table('conversation_memories').select('*').eq(
                'session_id', conversation_id
            ).order('created_at', desc=True).execute()

            memories = []
            if result.data:
                for memory in result.data:
                    memories.append({
                        'id': memory.get('id'),
                        'conversation_id': conversation_id,
                        'memory_text': memory.get('key_insights', ''),
                        'importance_score': memory.get('importance_score', 6.0),
                        'created_at': memory.get('created_at'),
                        'metadata': {
                            'type': 'dynamic_interaction',
                            'source_table': 'conversation_memories'
                        }
                    })

            logger.info(f"   📊 Database query: {len(memories)} dynamic memories")
            return memories

        except Exception as e:
            logger.error(f"Failed to get dynamic memories: {e}")
            return []

    async def _create_session_summary(self, memories: List[Dict]) -> Optional[Dict]:
        """Create a summary memory before archiving - preserves key insights"""
        try:
            if not memories:
                return None
            
            # Find high-importance breakthrough moments
            key_moments = [m for m in memories if m.get('importance_score', 0) >= 8.0]
            dynamic_memories = [m for m in memories if m.get('metadata', {}).get('type') == 'dynamic_interaction']
            
            if not dynamic_memories:
                return None  # No dynamic memories to summarize
            
            # Analyze conversation patterns
            high_trust_count = len([m for m in dynamic_memories if 'trust' in (m.get('memory_text') or '').lower()])
            defensive_count = len([m for m in dynamic_memories if 'defensive' in (m.get('memory_text') or '').lower()])

            # Extract topics mentioned
            all_text = ' '.join([m.get('memory_text') or '' for m in dynamic_memories])
            topics = []
            topic_keywords = {
                'work': ['job', 'work', 'career', 'boss'],
                'family': ['family', 'parent', 'child'],
                'anxiety': ['anxiety', 'worry', 'stress'],
                'goals': ['goal', 'future', 'plan']
            }
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in all_text.lower() for keyword in keywords):
                    topics.append(topic)
            
            # Create summary based on conversation arc
            if len(key_moments) >= 3:
                summary_text = f"Session summary: {len(key_moments)} breakthrough moments. Significant trust building and openness."
                importance = 9.0
            elif high_trust_count > defensive_count:
                summary_text = f"Session summary: Positive progression with {high_trust_count} trust-building moments."
                importance = 8.5
            elif defensive_count > high_trust_count:
                summary_text = f"Session summary: Challenging session with {defensive_count} defensive reactions. Approach needs adjustment."
                importance = 8.0
            else:
                summary_text = f"Session summary: Mixed session with {len(dynamic_memories)} interactions. Some progress made."
                importance = 7.5
            
            if topics:
                summary_text += f" Key topics: {', '.join(topics)}."
            
            return {
                'memory_text': summary_text,
                'importance_score': importance,
                'metadata': {
                    'type': 'session_summary',
                    'key_moments_count': len(key_moments),
                    'total_interactions': len(dynamic_memories),
                    'topics': topics
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create session summary: {e}")
            return None
    
    async def _ensure_archive_table_exists(self):
        """Ensure the archived_persona_memories table exists"""
        # This would typically be handled by a migration
        # For now, we'll just log that it should exist
        logger.info("Assuming archived_persona_memories table exists (should be created by migration)")
    
    def _analyze_memory_quality(self, memories: List[Dict]) -> Dict:
        """Analyze the quality distribution of memories"""
        if not memories:
            return {}
        
        quality_distribution = {
            "core_memories": 0,      # 8.5+
            "important_memories": 0, # 6.0-8.4
            "regular_memories": 0,   # 4.0-5.9
            "background_memories": 0 # <4.0
        }
        
        for memory in memories:
            importance = memory.get('importance_score', 0)
            if importance >= 8.5:
                quality_distribution["core_memories"] += 1
            elif importance >= 6.0:
                quality_distribution["important_memories"] += 1
            elif importance >= 4.0:
                quality_distribution["regular_memories"] += 1
            else:
                quality_distribution["background_memories"] += 1
        
        return quality_distribution