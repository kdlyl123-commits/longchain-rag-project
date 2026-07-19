"""RAG 链组装：检索 + 重排序 + LLM 生成"""

import json
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


def build_rag_chain(query: str, history_messages: list[dict] | None = None):
    """
    构建 RAG 流程：
    1. 检索 top-10
    2. 重排序取 top-5
    3. 组装 Prompt
    4. 流式生成
    """
    # 1. 检索
    docs = get_retrieved_documents(query, top_k=10)

    # 2. 重排序
    if len(docs) > 5:
        doc_texts = [d.page_content for d in docs]
        rerank_results = rerank(query, doc_texts, top_n=5)

        # 按重排序结果重建文档列表
        reranked_docs = []
        for item in rerank_results:
            idx = item["index"]
            if idx < len(docs):
                doc = docs[idx]
                doc.metadata["rerank_score"] = item["relevance_score"]
                reranked_docs.append(doc)
        docs = reranked_docs

    # 3. 构建知识库上下文（带编号）
    context_parts = []
    citations = []
    for i, doc in enumerate(docs):
        context_parts.append(f"[{i + 1}] {doc.page_content}")
        citations.append({
            "index": i + 1,
            "text": doc.page_content[:200],  # 截取前 200 字
            "filename": doc.metadata.get("filename", "未知"),
            "score": round(doc.metadata.get("rerank_score", 0), 4),
        })

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


async def stream_rag_response(query: str, history_messages: list[dict] | None = None) -> AsyncIterator[str]:
    """流式 RAG 回答生成器"""
    stream, citations = build_rag_chain(query, history_messages)

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
