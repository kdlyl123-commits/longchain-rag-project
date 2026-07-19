"""百炼 Embedding 模型封装 — 直接用 OpenAI 客户端，绕过 langchain-openai 兼容问题"""

from typing import List
from openai import OpenAI
from langchain_core.embeddings import Embeddings
from app.config import get_settings

_embeddings = None


class DashScopeEmbeddings(Embeddings):
    """百炼 Embedding，直接调用 OpenAI 兼容 API"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文档"""
        embeddings: List[List[float]] = []
        # 分批处理，每批最多 10 条
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self._client.embeddings.create(model=self.model, input=batch)
            embeddings.extend([d.embedding for d in resp.data])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """向量化单个查询"""
        resp = self._client.embeddings.create(model=self.model, input=text)
        return resp.data[0].embedding


def get_embeddings() -> DashScopeEmbeddings:
    """获取 Embeddings 实例（单例）"""
    global _embeddings
    if _embeddings is None:
        settings = get_settings()
        _embeddings = DashScopeEmbeddings(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            model=settings.embedding_model,
        )
    return _embeddings
