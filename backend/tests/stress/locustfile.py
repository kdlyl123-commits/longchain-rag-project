"""
RAG 知识库问答系统 — 压力测试主入口

启动方式:
    cd backend/tests/stress
    locust -f locustfile.py --host=http://localhost:8000

然后打开浏览器访问 http://localhost:8089

场景说明:
    AuthStressUser    — 认证压测（注册/登录/个人信息）
    RAGStressUser     — RAG 问答压测（★核心：SSE 流式问答）
    AdminDocStressUser — 管理员知识库浏览
"""

import sys
import os

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.tests.stress.scenarios.auth_scenario import AuthStressUser
from backend.tests.stress.scenarios.rag_scenario import RAGStressUser, AdminDocStressUser

# Locust 会自动发现所有继承 HttpUser 的类
# 如果需要只跑某个场景，在 Web UI 里可以单独选择
