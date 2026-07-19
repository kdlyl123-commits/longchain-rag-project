import io
import os
import uuid
import shutil
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.config import get_settings
from app.models.document import Document, DocumentChunk

settings = get_settings()

# 判断存储模式
USE_LOCAL_STORAGE = settings.storage_mode == "local" or not settings.minio_endpoint


# ============================================================
# 本地文件存储
# ============================================================
def _get_upload_dir() -> str:
    """获取上传目录的绝对路径"""
    base = os.path.dirname(os.path.dirname(__file__))  # backend/app/..
    upload_dir = os.path.join(base, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _sanitize_filename(filename: str) -> str:
    """消毒文件名，移除路径穿越字符和特殊字符"""
    import re
    # 只保留安全字符：中文、字母、数字、下划线、点、短横线
    safe = re.sub(r'[^\w一-鿿\.\-]', '_', filename)
    # 移除路径穿越序列
    safe = safe.replace('..', '').replace('/', '_').replace('\\', '_')
    return safe or 'unnamed'


def _local_upload(file_content: bytes, filename: str) -> str:
    """上传到本地文件系统，返回相对路径"""
    safe_name = _sanitize_filename(filename)
    date_prefix = datetime.now().strftime("%Y/%m/%d")
    dir_path = os.path.join(_get_upload_dir(), date_prefix)
    os.makedirs(dir_path, exist_ok=True)

    object_name = f"{date_prefix}/{uuid.uuid4().hex}_{safe_name}"
    file_path = os.path.join(_get_upload_dir(), object_name)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return object_name


def _local_download(object_name: str) -> bytes:
    """从本地文件系统下载"""
    file_path = os.path.join(_get_upload_dir(), object_name)
    with open(file_path, "rb") as f:
        return f.read()


def _local_delete(object_name: str):
    """从本地文件系统删除"""
    file_path = os.path.join(_get_upload_dir(), object_name)
    if os.path.exists(file_path):
        # 同时尝试清理空目录
        os.remove(file_path)
        parent = os.path.dirname(file_path)
        if not os.listdir(parent):
            os.rmdir(parent)


# ============================================================
# MinIO 存储（Docker 模式）
# ============================================================
_minio_client = None


def _get_minio_client():
    global _minio_client
    if _minio_client is None:
        from minio import Minio
        endpoint = settings.minio_endpoint.replace("http://", "").replace("https://", "")
        _minio_client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
    return _minio_client


def _ensure_bucket():
    client = _get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def _minio_upload(file_content: bytes, filename: str) -> str:
    """上传到 MinIO，返回对象路径"""
    from minio.error import S3Error
    client = _get_minio_client()
    _ensure_bucket()

    date_prefix = datetime.now().strftime("%Y/%m/%d")
    object_name = f"{date_prefix}/{uuid.uuid4().hex}_{filename}"

    content_type_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "md": "text/markdown",
        "csv": "text/csv",
    }

    client.put_object(
        settings.minio_bucket,
        object_name,
        data=io.BytesIO(file_content),
        length=len(file_content),
        content_type=content_type_map.get(
            filename.rsplit(".", 1)[-1].lower() if "." in filename else "", "application/octet-stream"
        ),
    )
    return object_name


def _minio_download(object_name: str) -> bytes:
    client = _get_minio_client()
    response = client.get_object(settings.minio_bucket, object_name)
    return response.read()


def _minio_delete(object_name: str):
    from minio.error import S3Error
    client = _get_minio_client()
    try:
        client.remove_object(settings.minio_bucket, object_name)
    except S3Error:
        pass


# ============================================================
# 统一接口
# ============================================================
def upload_file(file_content: bytes, filename: str) -> str:
    if USE_LOCAL_STORAGE:
        return _local_upload(file_content, filename)
    return _minio_upload(file_content, filename)


def download_file(object_name: str) -> bytes:
    if USE_LOCAL_STORAGE:
        return _local_download(object_name)
    return _minio_download(object_name)


def delete_file(object_name: str):
    if USE_LOCAL_STORAGE:
        _local_delete(object_name)
    else:
        _minio_delete(object_name)


def ensure_storage():
    """确保存储就绪（MinIO 模式才需要创建 bucket）"""
    if not USE_LOCAL_STORAGE:
        _ensure_bucket()


# ============================================================
# 业务方法
# ============================================================
async def create_document(
    db: AsyncSession,
    filename: str,
    file_content: bytes,
    file_type: str,
    file_size: int,
    user_id: int,
) -> Document:
    """创建文档记录并触发异步处理"""
    file_path = upload_file(file_content, filename)

    doc = Document(
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        file_path=file_path,
        status="processing",
        uploaded_by=user_id,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # 触发处理（有 Celery 用异步，没有则本地线程处理）
    from app.tasks.document_tasks import process_document, process_document_sync
    if process_document is not None:
        process_document.delay(doc.id)
    else:
        process_document_sync(doc.id)

    return doc


async def get_documents(
    db: AsyncSession, page: int = 1, page_size: int = 10
) -> tuple[list[Document], int]:
    """分页获取文档列表"""
    count_result = await db.execute(select(func.count(Document.id)))
    total = count_result.scalar()

    result = await db.execute(
        select(Document)
        .order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_document_chunks(db: AsyncSession, document_id: int) -> list[DocumentChunk]:
    """获取文档的所有切片"""
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    return list(result.scalars().all())


async def delete_document(db: AsyncSession, document_id: int):
    """删除文档及其向量"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise ValueError("文档不存在")

    # 删除存储文件
    delete_file(doc.file_path)

    # 删除向量
    try:
        from app.rag.vector_store import get_vector_store
        vector_store = get_vector_store()
        chunks = await get_document_chunks(db, document_id)
        vector_ids = [c.vector_id for c in chunks if c.vector_id]
        if vector_ids:
            vector_store.delete(ids=vector_ids)
    except Exception:
        pass

    await db.delete(doc)
    await db.flush()


async def get_knowledge_stats(db: AsyncSession) -> dict:
    """获取知识库统计"""
    doc_count = await db.execute(select(func.count(Document.id)))
    chunk_count = await db.execute(select(func.count(DocumentChunk.id)))
    token_sum = await db.execute(select(func.sum(DocumentChunk.token_count)))

    return {
        "document_count": doc_count.scalar() or 0,
        "chunk_count": chunk_count.scalar() or 0,
        "total_tokens": token_sum.scalar() or 0,
    }
