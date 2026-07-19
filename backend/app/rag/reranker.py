"""百炼 Rerank 重排序"""

import httpx
from app.config import get_settings


def rerank(
    query: str,
    documents: list[str],
    top_n: int = 5,
    return_documents: bool = True,
) -> list[dict]:
    """
    调用百炼 qwen3-rerank API 对检索结果重排序。

    Args:
        query: 用户问题
        documents: 候选文档列表
        top_n: 返回 top N 条结果
        return_documents: 是否返回原文

    Returns:
        [{"index": int, "relevance_score": float, "document": str}, ...]
    """
    settings = get_settings()

    # 百炼 Rerank OpenAI 兼容接口
    base_url = settings.dashscope_base_url.rstrip("/")
    url = f"{base_url}/rerank"

    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.rerank_model,
        "input": {
            "query": query,
            "documents": documents,
        },
        "parameters": {
            "top_n": top_n,
            "return_documents": return_documents,
        },
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

    # 解析返回结果
    results = []
    for item in result.get("output", {}).get("results", []):
        results.append({
            "index": item.get("index"),
            "relevance_score": item.get("relevance_score", 0),
            "document": item.get("document", {}).get("text", ""),
        })

    return results
