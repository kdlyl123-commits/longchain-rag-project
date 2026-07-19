"""RAG 链组装：检索 + 重排序 + LLM 生成"""

import json
import asyncio
from typing import AsyncIterator
from langchain.schema import Document
from app.rag.retriever import get_retrieved_documents
from app.rag.reranker import rerank
from app.rag.llm import get_llm


RAG_SYSTEM_PROMPT = """你是一个专业的电商客服助手，专门回答用户关于商品的问题。

请严格遵循以下规则：
1. 只能基于下面提供的"知识库内容"来回答问题
2. 如果知识库内容不足以回答问题，请明确告知用户"根据现有信息无法回答该问题"，不要编造信息
3. 在你的回答中，使用 [1] [2] [3] 等编号标注引用了哪个知识库片段
4. 回答要清晰、准确、友好

## 知识库内容：
{context}

## 对话历史：
{history}
"""


DRY_RUN_RESPONSE = "这是压测干跑模式的模拟回复。在实际生产环境中，这里会由大模型基于知识库内容生成回答。本条回复不消耗任何 API Token。"


def build_rag_chain(query: str, history_messages: list[dict] | None = None, dry_run: bool = False):
    """
    构建 RAG 流程：
    1. 检索 top-10
    2. 重排序取 top-5
    3. 组装 Prompt
    4. 流式生成

    dry_run=True: 跳过 Embedding/LLM API 调用，使用模拟响应，不消耗 Token
    """
    # 干跑模式：跳过所有 API 调用，返回模拟数据
    if dry_run:
        return _dry_run_chain(query), _dry_run_citations(query)

    # 1. 检索
    docs = get_retrieved_documents(query, top_k=10)

    # 2. 重排序（文档多时才做，少时直接用向量分数）
    if len(docs) > 5:
        doc_texts = [d.page_content for d in docs]
        rerank_results = rerank(query, doc_texts, top_n=5)
        reranked_docs = []
        for item in rerank_results:
            idx = item["index"]
            if idx < len(docs):
                doc = docs[idx]
                doc.metadata["final_score"] = item["relevance_score"]
                reranked_docs.append(doc)
        docs = reranked_docs
    else:
        # 文档少时，用向量检索分数，归一化到 0~1
        for doc in docs:
            raw_score = doc.metadata.get("vector_score", 0.5)
            # Chroma 返回的是距离，越小越相关，转为 0~1
            doc.metadata["final_score"] = round(max(0, min(1, 1 - raw_score)), 4)

    # 3. 按分数排序
    docs_sorted = sorted(docs, key=lambda d: d.metadata.get("final_score", 0), reverse=True)

    # 全部文档给 LLM 做上下文
    context_parts = []
    for i, doc in enumerate(docs_sorted):
        context_parts.append(f"[{i + 1}] {doc.page_content}")

    # 只取 top-3，且相关度 > 0 作为引用展示（保留原始编号匹配 LLM 引用标记）
    citations = []
    for i, doc in enumerate(docs_sorted):
        score_pct = round(doc.metadata.get("final_score", 0) * 100, 1)
        if score_pct <= 0:
            continue
        full_text = doc.page_content
        preview = full_text[:50] + ("..." if len(full_text) > 50 else "")
        citations.append({
            "index": i + 1,  # 保持和 LLM 上下文 [n] 一致的编号
            "text": full_text,
            "preview": preview,
            "filename": doc.metadata.get("filename", "未知"),
            "score": score_pct,
        })
        if len(citations) >= 3:
            break

    context = "\n\n".join(context_parts)

    # 4. 构建对话历史
    history_str = ""
    if history_messages:
        for msg in history_messages[-6:]:  # 只保留最近 3 轮对话
            role_label = "用户" if msg["role"] == "user" else "助手"
            history_str += f"{role_label}: {msg['content']}\n"

    # 5. 组装完整 Prompt
    system_prompt = RAG_SYSTEM_PROMPT.format(context=context, history=history_str)

    # 6. 返回生成器和引用信息
    llm = get_llm("main")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    return llm.astream(messages), citations


def _dry_run_chain(query: str):
    """干跑模式：返回模拟的流式生成器（不调用 LLM API）"""
    async def _mock_stream():
        class MockChunk:
            def __init__(self, text):
                self.content = text

        response = DRY_RUN_RESPONSE
        for i in range(0, len(response), 5):
            await asyncio.sleep(0.05)  # 模拟 LLM 网络延迟
            yield MockChunk(response[i : i + 5])
    return _mock_stream()


def _dry_run_citations(query: str) -> list[dict]:
    """干跑模式：返回模拟引用"""
    return [
        {
            "index": 1,
            "text": "这是压测干跑模式下的模拟知识库片段。实际引用会包含真实的文档内容。",
            "preview": "这是压测干跑模式下的模拟知识库片段...",
            "filename": "dry_run_sample.txt",
            "score": 95.0,
        }
    ]


async def stream_rag_response(
    query: str,
    history_messages: list[dict] | None = None,
    dry_run: bool = False,
) -> AsyncIterator[str]:
    """流式 RAG 回答生成器"""
    stream, citations = build_rag_chain(query, history_messages, dry_run)

    # 先发送引用信息
    yield f"data: {json.dumps({'type': 'citations', 'citations': citations}, ensure_ascii=False)}\n\n"

    # 再流式发送回答内容
    async for chunk in stream:
        if chunk.content:
            content = chunk.content
            # 确保是字符串
            if isinstance(content, list):
                content = "".join(content)
            yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"
