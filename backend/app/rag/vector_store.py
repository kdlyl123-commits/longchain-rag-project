"""向量数据库封装：自动切换嵌入式和服务模式"""

import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from app.config import get_settings
from app.rag.embeddings import get_embeddings

_vector_store = None
_collection_name = "knowledge_base"


def get_vector_store() -> Chroma:
    """获取向量数据库实例（单例），自动选择嵌入式或服务模式"""
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        embeddings = get_embeddings()

        if settings.chroma_host:
            # === 服务模式（Docker Chroma 容器）===
            chroma_client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        else:
            # === 嵌入式模式（本地开发）===
            persist_dir = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data")
            persist_dir = os.path.abspath(persist_dir)
            os.makedirs(persist_dir, exist_ok=True)
            chroma_client = chromadb.PersistentClient(
                path=persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

        _vector_store = Chroma(
            client=chroma_client,
            collection_name=_collection_name,
            embedding_function=embeddings,
        )

    return _vector_store


def get_retriever(k: int = 10):
    """获取检索器"""
    vector_store = get_vector_store()
    return vector_store.as_retriever(search_kwargs={"k": k})
