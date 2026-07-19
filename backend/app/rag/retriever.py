"""混合检索器：向量检索 + BM25 关键词检索"""

from typing import List
from langchain.schema import Document
from app.rag.vector_store import get_vector_store


# ============================================================
# BM25 关键词检索（内存实现）
# ============================================================
class BM25Retriever:
    """
    简易 BM25 检索器。
    用于对查询进行关键词级别的精确匹配，
    弥补向量检索在精确关键词（如商品型号 SKU-12345）上的不足。
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Document] = []
        self.doc_freqs: dict = {}  # 词 → 包含该词的文档数
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0
        self._built = False

    def fit(self, documents: List[Document]):
        """构建 BM25 索引"""
        import re
        self.documents = documents
        self.doc_freqs = {}
        self.doc_lengths = []
        total_length = 0

        for doc in documents:
            words = set(re.findall(r'\w+', doc.page_content.lower()))
            for word in words:
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1
            length = len(re.findall(r'\w+', doc.page_content.lower()))
            self.doc_lengths.append(length)
            total_length += length

        self.avg_doc_length = total_length / len(documents) if documents else 1
        self._built = True

    def search(self, query: str, k: int = 10) -> List[tuple[int, float]]:
        """搜索并返回 (文档索引, 分数) 列表"""
        import re
        import math

        if not self._built or not self.documents:
            return []

        query_words = re.findall(r'\w+', query.lower())
        N = len(self.documents)
        scores = []

        for idx, doc in enumerate(self.documents):
            score = 0
            doc_words = re.findall(r'\w+', doc.page_content.lower())
            doc_len = self.doc_lengths[idx]

            for word in query_words:
                if word not in self.doc_freqs:
                    continue
                df = self.doc_freqs[word]
                tf = doc_words.count(word)

                idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                score += idf * numerator / denominator

            if score > 0:
                scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


# ============================================================
# 混合检索
# ============================================================
_bm25_index: BM25Retriever | None = None
_bm25_doc_list: List[Document] = []


def _rebuild_bm25_if_needed(vector_store):
    """如果需要，从向量数据库中重建 BM25 索引"""
    global _bm25_index, _bm25_doc_list
    try:
        # 从 Chroma 获取所有文档
        collection = vector_store._collection
        results = collection.get()
        if results and results.get("documents"):
            docs = []
            for text, metadata in zip(results["documents"], results["metadatas"]):
                docs.append(Document(page_content=text, metadata=metadata or {}))
            if len(docs) != len(_bm25_doc_list):
                _bm25_doc_list = docs
                _bm25_index = BM25Retriever()
                _bm25_index.fit(docs)
    except Exception:
        # 如果 BM25 构建失败，静默降级
        pass


def hybrid_search(query: str, k: int = 10) -> List[Document]:
    """
    混合检索：向量检索 + BM25 关键词检索。

    1. 向量检索取 top-K（语义匹配）
    2. BM25 关键词检索取 top-K（精确匹配）
    3. 合并去重后返回
    """
    vector_store = get_vector_store()
    _rebuild_bm25_if_needed(vector_store)

    # 向量检索（带分数）
    vector_results = vector_store.similarity_search_with_score(query, k=k)
    vector_docs = []
    for doc, score in vector_results:
        doc.metadata["vector_score"] = round(float(score), 4)
        vector_docs.append(doc)

    # BM25 关键词检索
    bm25_docs = []
    if _bm25_index and _bm25_index._built:
        bm25_results = _bm25_index.search(query, k=k)
        for idx, score in bm25_results:
            if idx < len(_bm25_doc_list):
                doc = _bm25_doc_list[idx]
                doc.metadata["bm25_score"] = score
                bm25_docs.append(doc)

    # 合并去重（基于文本内容）
    seen_texts = set()
    merged = []

    # 向量检索结果优先
    for doc in vector_docs:
        text_key = doc.page_content[:100]
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            doc.metadata["source"] = "vector"
            merged.append(doc)

    # 添加 BM25 独有的结果
    for doc in bm25_docs:
        text_key = doc.page_content[:100]
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            doc.metadata["source"] = "bm25"
            merged.append(doc)

    return merged[:k]


def get_retrieved_documents(query: str, top_k: int = 10) -> List[Document]:
    """执行混合检索，返回相关文档片段"""
    return hybrid_search(query, k=top_k)
