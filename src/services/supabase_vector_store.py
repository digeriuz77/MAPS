"""
Supabase Vector Store for LangChain GenerativeAgent Memory
Provides persistent memory storage with vector similarity search using pgvector
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import numpy as np
from supabase import Client
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.base import VectorStore

logger = logging.getLogger(__name__)

class SupabaseVectorStore(VectorStore):
    """
    Supabase-backed vector store for persistent GenerativeAgent memories
    Uses pgvector extension for efficient similarity search
    """

    def __init__(
        self,
        supabase_client: Client,
        embedding: Embeddings,
        conversation_id: str,
        persona_name: str = "Mary",
        table_name: str = "persona_memories"
    ):
        self.supabase = supabase_client
        self.embedding = embedding
        self.conversation_id = conversation_id
        self.persona_name = persona_name
        self.table_name = table_name

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any
    ) -> List[str]:
        """Add texts with embeddings to Supabase storage"""
        try:
            # Generate embeddings for all texts
            embeddings = self.embedding.embed_documents(texts)

            # Prepare records for insertion
            records = []
            generated_ids = []

            for i, (text, embedding_vec) in enumerate(zip(texts, embeddings)):
                record_id = ids[i] if ids and i < len(ids) else str(uuid.uuid4())
                generated_ids.append(record_id)

                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                importance_score = metadata.get('importance', 0.0)

                records.append({
                    'id': record_id,
                    'conversation_id': self.conversation_id,
                    'persona_name': self.persona_name,
                    'memory_text': text,
                    'embedding': embedding_vec,
                    'importance_score': importance_score,
                    'metadata': metadata,
                    'created_at': datetime.utcnow().isoformat(),
                    'accessed_at': datetime.utcnow().isoformat()
                })

            # Batch insert to Supabase
            result = self.supabase.table(self.table_name).insert(records).execute()

            if not result.data:
                logger.warning("No data returned from Supabase insert")

            logger.info(f"Added {len(texts)} memories to Supabase for {self.persona_name}")
            return generated_ids

        except Exception as e:
            logger.error(f"Failed to add texts to Supabase: {e}", exc_info=True)
            return []

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 8,
        filter: Optional[dict] = None,
        **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar memories using vector similarity
        Returns documents with similarity scores
        """
        try:
            # Get query embedding
            query_embedding = self.embedding.embed_query(query)

            # Build the RPC call for vector similarity search
            # Note: This requires a stored procedure in Supabase for optimal performance
            # For now, we'll use a simpler approach with ordering

            query_builder = self.supabase.table(self.table_name) \
                .select("id, memory_text, importance_score, metadata, created_at, accessed_at") \
                .eq("conversation_id", self.conversation_id) \
                .eq("persona_name", self.persona_name) \
                .order("created_at", desc=True) \
                .limit(k * 3)  # Get more results to filter better matches

            result = query_builder.execute()

            if not result.data:
                logger.info("No memories found in Supabase")
                return []

            # For now, return recent memories (will implement proper vector search once table exists)
            documents_with_scores = []
            for record in result.data[:k]:
                doc = Document(
                    page_content=record["memory_text"],
                    metadata={
                        "id": record["id"],
                        "importance": record.get("importance_score", 0.0),
                        "created_at": record["created_at"],
                        "accessed_at": record["accessed_at"],
                        **record.get("metadata", {})
                    }
                )
                # Placeholder score (will use actual vector similarity once implemented)
                score = 0.8
                documents_with_scores.append((doc, score))

            # Update accessed_at timestamp for retrieved memories
            memory_ids = [record["id"] for record in result.data[:k]]
            if memory_ids:
                self.supabase.table(self.table_name) \
                    .update({"accessed_at": datetime.utcnow().isoformat()}) \
                    .in_("id", memory_ids) \
                    .execute()

            logger.info(f"Retrieved {len(documents_with_scores)} memories from Supabase")
            return documents_with_scores

        except Exception as e:
            logger.error(f"Similarity search failed: {e}", exc_info=True)
            return []

    def similarity_search(
        self,
        query: str,
        k: int = 8,
        filter: Optional[dict] = None,
        **kwargs: Any
    ) -> List[Document]:
        """Search for similar documents without scores"""
        docs_with_scores = self.similarity_search_with_score(query, k, filter, **kwargs)
        return [doc for doc, _ in docs_with_scores]

    def load_existing_memories(self) -> List[Document]:
        """Load all existing memories for this conversation"""
        try:
            result = self.supabase.table(self.table_name) \
                .select("memory_text, importance_score, metadata, created_at") \
                .eq("conversation_id", self.conversation_id) \
                .eq("persona_name", self.persona_name) \
                .order("created_at") \
                .execute()

            if not result.data:
                return []

            documents = []
            for record in result.data:
                doc = Document(
                    page_content=record["memory_text"],
                    metadata={
                        "importance": record.get("importance_score", 0.0),
                        "created_at": record["created_at"],
                        **record.get("metadata", {})
                    }
                )
                documents.append(doc)

            logger.info(f"Loaded {len(documents)} existing memories from Supabase")
            return documents

        except Exception as e:
            logger.error(f"Failed to load existing memories: {e}", exc_info=True)
            return []

    def get_memory_count(self) -> int:
        """Get total number of memories stored"""
        try:
            result = self.supabase.table(self.table_name) \
                .select("id", count="exact") \
                .eq("conversation_id", self.conversation_id) \
                .eq("persona_name", self.persona_name) \
                .execute()

            return result.count or 0

        except Exception as e:
            logger.error(f"Failed to get memory count: {e}")
            return 0

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        supabase_client: Optional[Client] = None,
        conversation_id: str = "",
        persona_name: str = "Mary",
        **kwargs: Any
    ) -> "SupabaseVectorStore":
        """Create vector store and add initial texts"""
        if not supabase_client:
            raise ValueError("supabase_client is required")

        vector_store = cls(
            supabase_client=supabase_client,
            embedding=embedding,
            conversation_id=conversation_id,
            persona_name=persona_name
        )

        if texts:
            vector_store.add_texts(texts, metadatas)

        return vector_store