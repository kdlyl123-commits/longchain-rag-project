"""
场景B：RAG 问答压测（★ 核心）
测试 SSE 流式问答、会话管理

运行：
    python -m locust -f locustfile_rag.py --host=http://localhost:8000
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from backend.tests.stress.scenarios.rag_scenario import RAGStressUser
