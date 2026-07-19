from datetime import datetime
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    token_count: int

    model_config = {"from_attributes": True}


class KnowledgeStatsResponse(BaseModel):
    document_count: int
    chunk_count: int
    total_tokens: int
