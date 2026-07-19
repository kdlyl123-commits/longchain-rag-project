"""百炼 Embedding 模型封装"""

from langchain_openai import OpenAIEmbeddings
from app.config import get_settings

_embeddings = None


def get_embeddings() -> OpenAIEmbeddings:
    """获取 Embeddings 实例（单例）"""
    global _embeddings
    if _embeddings is None:
        settings = get_settings()
        _embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.dashscope_api_key,
            openai_api_base=settings.dashscope_base_url,
            dimensions=settings.embedding_dimensions,
        )
    return _embeddings
