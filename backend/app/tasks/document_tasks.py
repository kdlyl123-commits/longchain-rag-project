"""文档处理任务：Celery 异步 或 本地同步"""

from app.database import sync_engine
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentChunk
from app.config import get_settings

settings = get_settings()


def _process_document_impl(document_id: int):
    """文档处理核心逻辑（无论 Celery 还是本地都走这个）"""
    with Session(sync_engine) as db:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return {"status": "error", "message": "Document not found"}

        try:
            doc.status = "processing"
            db.commit()

            from app.rag.loader import load_document
            from app.rag.splitter import split_documents
            from app.rag.embeddings import get_embeddings
            from app.rag.vector_store import get_vector_store

            raw_docs = load_document(doc.file_path, doc.file_type)
            chunks = split_documents(raw_docs)

            embeddings = get_embeddings()
            vector_store = get_vector_store()

            texts = [chunk.page_content for chunk in chunks]
            metadatas = [
                {
                    "doc_id": str(doc.id),
                    "filename": doc.filename,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ]

            vector_ids = vector_store.add_texts(texts, metadatas)

            for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk.page_content,
                    vector_id=vector_id,
                    token_count=len(chunk.page_content) // 2,
                )
                db.add(db_chunk)

            doc.status = "done"
            doc.chunk_count = len(chunks)
            db.commit()

            return {"status": "done", "chunk_count": len(chunks)}

        except Exception as e:
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()
            raise


# 如果有 Celery，注册为 Celery 任务
from app.celery_app import celery_app
if celery_app is not None:

    @celery_app.task(bind=True, max_retries=3)
    def process_document(self, document_id: int):
        try:
            return _process_document_impl(document_id)
        except Exception as e:
            raise self.retry(exc=e, countdown=60)

else:
    # 没有 Celery 时，提供同步版本供本地调用
    process_document = None


def process_document_sync(document_id: int):
    """在后台线程处理文档，错误会打印到终端"""
    import threading
    import traceback

    def _safe_process():
        try:
            result = _process_document_impl(document_id)
            print(f"[DocProcessor] 文档#{document_id} 处理完成: {result}")
        except Exception:
            print(f"[DocProcessor] 文档#{document_id} 处理失败:")
            traceback.print_exc()

    t = threading.Thread(target=_safe_process, daemon=False)
    t.start()
    return t
