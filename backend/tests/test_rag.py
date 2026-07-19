"""RAG 模块单元测试"""

import pytest
from unittest.mock import patch, MagicMock


class TestEmbeddings:
    def test_get_embeddings_singleton(self):
        from app.rag.embeddings import get_embeddings
        e1 = get_embeddings()
        e2 = get_embeddings()
        assert e1 is e2  # 单例模式

    def test_embedding_config(self):
        from app.rag.embeddings import get_embeddings
        from app.config import get_settings
        settings = get_settings()
        emb = get_embeddings()
        assert emb.model == settings.embedding_model


class TestLLM:
    def test_get_llm_returns_different_models(self):
        from app.rag.llm import get_llm
        main = get_llm("main")
        simple = get_llm("simple")
        complex_ = get_llm("complex")
        assert main.model_name != simple.model_name

    def test_get_llm_singleton(self):
        from app.rag.llm import get_llm
        a = get_llm("main")
        b = get_llm("main")
        assert a is b


class TestSplitter:
    def test_split_plain_text(self):
        from app.rag.splitter import split_documents
        from langchain.schema import Document
        docs = [Document(page_content="段落一。段落二。段落三。" * 100)]
        chunks = split_documents(docs, chunk_size=100, chunk_overlap=10)
        assert len(chunks) > 1
        # 每个 chunk 不应该超过 chunk_size
        for c in chunks:
            assert len(c.page_content) <= 100

    def test_split_markdown(self):
        from app.rag.splitter import split_documents
        from langchain.schema import Document
        md = """# 标题一
        内容一内容一。

        ## 标题二
        内容二内容二。

        ### 标题三
        内容三内容三。"""
        docs = [Document(page_content=md)]
        chunks = split_documents(docs, chunk_size=200, chunk_overlap=20)
        assert len(chunks) >= 1


class TestRetriever:
    def test_bm25_fit_and_search(self):
        from app.rag.retriever import BM25Retriever
        from langchain.schema import Document
        docs = [
            Document(page_content="iPhone 15 价格 2999 元"),
            Document(page_content="华为 Mate 60 价格 3999 元"),
            Document(page_content="小米 14 价格 1999 元"),
        ]
        bm25 = BM25Retriever()
        bm25.fit(docs)
        results = bm25.search("iPhone", k=2)
        assert len(results) > 0
        # 第一名应该包含 iPhone
        top_idx = results[0][0]
        assert "iPhone" in docs[top_idx].page_content

    def test_bm25_empty(self):
        from app.rag.retriever import BM25Retriever
        bm25 = BM25Retriever()
        results = bm25.search("test")
        assert results == []


class TestReranker:
    @patch("app.rag.reranker.httpx.Client")
    def test_rerank_basic(self, mock_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "output": {
                "results": [
                    {"index": 0, "relevance_score": 0.95, "document": {"text": "doc0"}},
                    {"index": 2, "relevance_score": 0.80, "document": {"text": "doc2"}},
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        from app.rag.reranker import rerank
        results = rerank("query", ["doc0", "doc1", "doc2"], top_n=2)
        assert len(results) == 2
        assert results[0]["index"] == 0
        assert results[0]["relevance_score"] == 0.95


class TestCache:
    def test_cache_set_get(self):
        from app.utils.cache import cache_set, cache_get, cache_delete
        cache_set("test_key", "test_value", ttl=60)
        assert cache_get("test_key") == "test_value"
        cache_delete("test_key")
        assert cache_get("test_key") is None

    def test_cache_ttl_expiry(self):
        from app.utils.cache import cache_set, cache_get
        cache_set("expire_key", "val", ttl=-1)  # 立即过期
        assert cache_get("expire_key") is None

    def test_cache_invalidate_pattern(self):
        from app.utils.cache import cache_set, cache_get, cache_invalidate_pattern
        cache_set("prefix:a", "1")
        cache_set("prefix:b", "2")
        cache_invalidate_pattern("prefix:*")
        assert cache_get("prefix:a") is None
        assert cache_get("prefix:b") is None
