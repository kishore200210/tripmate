"""
app/modules/rag/service.py

RAG Service — handles document loading, chunking, OpenAI embeddings, and Groq LLM querying.
"""

import logging
import os
import uuid
import glob
from typing import Any
from uuid import UUID

from groq import AsyncGroq
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.embeddings import EmbeddingService
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.modules.destinations.models import Destination, Document
from app.modules.destinations.repository import DestinationRepository
from app.modules.rag.repository import DocumentRepository
from app.modules.rag.schemas import RAGQueryRequest, RAGQueryResponse, SearchRequest, SearchResult
from app.modules.rag.retriever import RAGRetriever
from app.modules.rag.prompt import RAG_SYSTEM_PROMPT
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)

GLOBAL_KNOWLEDGE_DESTINATION_NAME = "Global Knowledge Base"


class RAGService(BaseService[DocumentRepository]):
    """Service layer for RAG operations."""

    def __init__(
        self,
        repository: DocumentRepository,
        destination_repository: DestinationRepository,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        super().__init__(repository=repository)
        self.destination_repository = destination_repository
        self.embedding_service = embedding_service or EmbeddingService()
        self.retriever = RAGRetriever(repository=self.repository, embedding_service=self.embedding_service)
        
        settings = get_settings()
        api_key = settings.GROQ_API_KEY.strip() if settings.GROQ_API_KEY else ""
        self.groq_client = AsyncGroq(api_key=api_key if api_key and api_key != "dummy-key" else "dummy-key")
        self.model = settings.GROQ_MODEL

    async def _get_or_create_global_destination(self) -> UUID:
        """Fetch or create a dummy destination for global documents."""
        # Using SQLAlchemy 2.0 select
        from sqlalchemy import select
        result = await self.destination_repository.db.execute(select(Destination).where(Destination.name == GLOBAL_KNOWLEDGE_DESTINATION_NAME))
        dest = result.scalars().first()
        if dest:
            return dest.id
        
        # Create it
        new_dest = Destination(
            id=uuid.uuid4(),
            name=GLOBAL_KNOWLEDGE_DESTINATION_NAME,
            country="Global",
            description="Hidden destination for global travel documents.",
        )
        await self.destination_repository.create(new_dest)
        return new_dest.id

    async def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Call EmbeddingService to generate embeddings in batches."""
        return await self.embedding_service.generate_embeddings(texts)

    async def reindex_all_documents(self) -> dict[str, Any]:
        """Reads all files in backend/travel_docs/, chunks, embeds, and stores them."""
        docs_dir = os.path.join(os.getcwd(), "travel_docs")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir, exist_ok=True)
            return {"message": "Created travel_docs directory. Please add files and try again.", "processed_chunks": 0}

        destination_id = await self._get_or_create_global_destination()

        # Clear existing documents for the global destination to reindex
        from sqlalchemy import delete
        await self.repository.db.execute(delete(Document).where(Document.destination_id == destination_id))
        await self.repository.db.commit()

        processed_chunks = 0
        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)

        for file_path in glob.glob(f"{docs_dir}/*"):
            if not os.path.isfile(file_path):
                continue
            
            filename = os.path.basename(file_path)
            ext = filename.lower().split('.')[-1]
            
            try:
                if ext == "pdf":
                    loader = PyPDFLoader(file_path)
                elif ext == "md":
                    # Unstructured requires more dependencies, we can just use TextLoader for MD
                    loader = TextLoader(file_path, encoding="utf-8")
                elif ext == "txt":
                    loader = TextLoader(file_path, encoding="utf-8")
                else:
                    logger.warning("Unsupported file type: %s", filename)
                    continue
                
                raw_docs = loader.load()
                chunks = splitter.split_documents(raw_docs)
                
                texts = [chunk.page_content for chunk in chunks]
                if not texts:
                    continue

                embeddings = await self._generate_embeddings(texts)
                
                for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                    doc = Document(
                        id=uuid.uuid4(),
                        title=f"{filename} - Part {i+1}",
                        content=text,
                        source_file=filename,
                        chunk_index=i,
                        embedding=embedding,
                        destination_id=destination_id,
                    )
                    self.repository.db.add(doc)
                
                processed_chunks += len(texts)
            except Exception as e:
                logger.error("Failed to process %s: %s", filename, str(e))
        
        await self.repository.db.commit()
        return {"message": "Reindex successful", "processed_chunks": processed_chunks}

    async def query_knowledge_base(self, payload: RAGQueryRequest) -> RAGQueryResponse:
        """RAG Pipeline: embed -> retrieve -> prompt -> Groq."""
        # 1. Retrieve Context
        retrieval_result = await self.retriever.retrieve_context(payload.query, limit=5)
        context = retrieval_result["context"]
        sources = retrieval_result["sources"]

        if not context:
            return RAGQueryResponse(
                answer="I couldn't find any relevant travel documents in my knowledge base to answer your question.",
                sources=[]
            )

        # 2. Format Prompt
        system_msg = RAG_SYSTEM_PROMPT.format(context=context)

        # 3. Call Groq
        try:
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": payload.query}
                ],
                temperature=0.3, # Low temp for grounded answers
            )
            answer = response.choices[0].message.content or "No answer generated."
        except Exception as e:
            logger.error("Groq Error during RAG: %s", str(e))
            answer = "Sorry, I encountered an error while trying to process your request."

        return RAGQueryResponse(answer=answer, sources=sources)

    async def get_status(self) -> dict[str, Any]:
        from sqlalchemy import select, func
        stmt = select(func.count()).select_from(Document)
        result = await self.repository.db.execute(stmt)
        count = result.scalar() or 0
        return {"total_chunks": count}

