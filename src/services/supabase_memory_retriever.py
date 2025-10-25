"""
Supabase-backed Memory Retriever for GenerativeAgent
Replaces FAISS with persistent Supabase storage and vector similarity search
"""

import math
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from supabase import Client
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain_community.docstore.base import Docstore
from langchain_community.docstore.in_memory import InMemoryDocstore

from .supabase_vector_store import SupabaseVectorStore

logger = logging.getLogger(__name__)

def create_supabase_memory_retriever(
    supabase_client: Client,
    embedding: Embeddings,
    conversation_id: str,
    persona_name: str = "Mary",
    k: int = 8
) -> TimeWeightedVectorStoreRetriever:
    """
    Create a memory retriever using Supabase for persistent storage
    Maintains compatibility with LangChain GenerativeAgent
    """

    # Create Supabase vector store
    vectorstore = SupabaseVectorStore(
        supabase_client=supabase_client,
        embedding=embedding,
        conversation_id=conversation_id,
        persona_name=persona_name
    )

    # Load existing memories from database
    existing_memories = vectorstore.load_existing_memories()
    logger.info(f"Loaded {len(existing_memories)} existing memories for {persona_name}")

    # Create time-weighted retriever with Supabase backend
    retriever = TimeWeightedVectorStoreRetriever(
        vectorstore=vectorstore,
        other_score_keys=["importance"],
        k=k,
        decay_rate=-0.01,  # Memories decay over time
        default_salience=0.0
    )

    # Add existing memories to in-memory docstore for LangChain compatibility
    if existing_memories:
        # The retriever needs the documents to be in the vectorstore's docstore
        # For Supabase, we'll populate this from database
        try:
            # Add existing memories back to the retriever's internal storage
            texts = [doc.page_content for doc in existing_memories]
            metadatas = [doc.metadata for doc in existing_memories]

            if texts:
                vectorstore.add_texts(texts, metadatas=metadatas)
                logger.info(f"Restored {len(texts)} memories to retriever")
        except Exception as e:
            logger.warning(f"Failed to restore memories to retriever: {e}")

    return retriever

class SupabaseMemoryDocstore(Docstore):
    """
    Custom docstore that reads from Supabase persona_memories table
    Provides seamless integration with existing LangChain memory system
    """

    def __init__(
        self,
        supabase_client: Client,
        conversation_id: str,
        persona_name: str = "Mary"
    ):
        self.supabase = supabase_client
        self.conversation_id = conversation_id
        self.persona_name = persona_name
        self._cache: Dict[str, Document] = {}

    def add(self, texts: Dict[str, Document]) -> None:
        """Add documents to the docstore"""
        for doc_id, document in texts.items():
            self._cache[doc_id] = document
            # Persist to Supabase
            self._persist_document(doc_id, document)

    def delete(self, ids: List[str]) -> None:
        """Delete documents from the docstore"""
        for doc_id in ids:
            if doc_id in self._cache:
                del self._cache[doc_id]
            # Delete from Supabase
            try:
                self.supabase.table("persona_memories") \
                    .delete() \
                    .eq("id", doc_id) \
                    .execute()
            except Exception as e:
                logger.warning(f"Failed to delete memory {doc_id}: {e}")

    def search(self, search: str) -> Document:
        """Search for a document by ID"""
        if search in self._cache:
            return self._cache[search]

        # Try to load from Supabase
        try:
            result = self.supabase.table("persona_memories") \
                .select("*") \
                .eq("id", search) \
                .single() \
                .execute()

            if result.data:
                doc = Document(
                    page_content=result.data["memory_text"],
                    metadata={
                        "importance": result.data.get("importance_score", 0.0),
                        "created_at": result.data["created_at"],
                        **result.data.get("metadata", {})
                    }
                )
                self._cache[search] = doc
                return doc

        except Exception as e:
            logger.warning(f"Failed to search memory {search}: {e}")

        raise KeyError(f"Document {search} not found")

    def _persist_document(self, doc_id: str, document: Document) -> None:
        """Persist a document to Supabase"""
        try:
            # Extract metadata
            importance = document.metadata.get("importance", 0.0)
            metadata = {k: v for k, v in document.metadata.items()
                       if k not in ["importance", "created_at", "accessed_at"]}

            # Upsert to Supabase
            record = {
                "id": doc_id,
                "conversation_id": self.conversation_id,
                "persona_name": self.persona_name,
                "memory_text": document.page_content,
                "importance_score": importance,
                "metadata": metadata,
                "accessed_at": datetime.utcnow().isoformat()
            }

            self.supabase.table("persona_memories").upsert(record).execute()

        except Exception as e:
            logger.warning(f"Failed to persist document {doc_id}: {e}")

    def load_all_memories(self) -> Dict[str, Document]:
        """Load all memories for this conversation from Supabase"""
        try:
            result = self.supabase.table("persona_memories") \
                .select("*") \
                .eq("conversation_id", self.conversation_id) \
                .eq("persona_name", self.persona_name) \
                .execute()

            memories = {}
            for record in result.data:
                doc = Document(
                    page_content=record["memory_text"],
                    metadata={
                        "importance": record.get("importance_score", 0.0),
                        "created_at": record["created_at"],
                        "accessed_at": record.get("accessed_at"),
                        **record.get("metadata", {})
                    }
                )
                memories[record["id"]] = doc
                self._cache[record["id"]] = doc

            logger.info(f"Loaded {len(memories)} memories from Supabase")
            return memories

        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
            return {}