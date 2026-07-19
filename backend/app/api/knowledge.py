from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.schemas.knowledge import (
    DocumentResponse,
    DocumentListResponse,
    DocumentChunkResponse,
    KnowledgeStatsResponse,
)
from app.services import document_service

router = APIRouter()

# 所有知识库接口都需要管理员权限
router.dependencies = [Depends(require_admin)]

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "md", "markdown", "csv"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """获取文档列表（分页）"""
    docs, total = await document_service.get_documents(db, page, page_size)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传文档"""
    # 校验文件扩展名
    if file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    else:
        ext = ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，允许: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 读取文件内容
    content = await file.read()

    # 校验文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件为空")

    try:
        doc = await document_service.create_document(
            db,
            filename=file.filename or "unknown",
            file_content=content,
            file_type=ext,
            file_size=len(content),
            user_id=current_user["id"],
        )
        return doc
    except Exception:
        import logging
        logging.getLogger(__name__).exception("文档上传处理失败")
        raise HTTPException(status_code=500, detail="上传失败，请稍后重试")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除文档（同步删除向量和文件）"""
    try:
        await document_service.delete_document(db, document_id)
        return {"message": "文档已删除"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def get_document_chunks(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取文档切片"""
    chunks = await document_service.get_document_chunks(db, document_id)
    return [DocumentChunkResponse.model_validate(c) for c in chunks]


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """重新处理失败的文档"""
    from sqlalchemy import select
    from app.models.document import Document

    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.status != "error":
        raise HTTPException(status_code=400, detail="只能重新处理失败的文档")

    # 清除旧的 chunks
    from sqlalchemy import delete
    from app.models.document import DocumentChunk

    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

    doc.status = "processing"
    doc.error_message = None
    await db.flush()

    # 重新触发处理（Celery 异步 或 本地线程）
    from app.tasks.document_tasks import process_document, process_document_sync
    if process_document is not None:
        process_document.delay(doc.id)
    else:
        process_document_sync(doc.id)

    return {"message": "已重新加入处理队列"}


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """获取知识库统计"""
    stats = await document_service.get_knowledge_stats(db)
    return KnowledgeStatsResponse(**stats)
