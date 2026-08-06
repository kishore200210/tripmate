"""
app/modules/rag/schemas.py

Pydantic v2 schemas for the RAG module.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IngestRequest(BaseModel):
    """Schema for POST /api/v1/rag/ingest"""
    destination_id: UUID = Field(..., description="The destination this document relates to.")
    file_path: str = Field(..., description="Absolute or relative path to the Markdown file.")


class SearchRequest(BaseModel):
    """Schema for POST /api/v1/rag/search"""
    destination_id: UUID = Field(..., description="The destination to filter documents by.")
    query: str = Field(..., min_length=2, max_length=1000, description="The search query.")
    limit: int = Field(5, ge=1, le=20, description="Max number of chunks to return.")


class SearchResult(BaseModel):
    """A single retrieved chunk with citations and score."""
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    title: str
    content: str
    source_file: str | None
    chunk_index: int
    score: float = Field(..., description="Cosine similarity or L2 distance score.")
