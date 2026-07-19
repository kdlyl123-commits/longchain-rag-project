"""
场景 B：RAG 问答压测（★ 核心场景）
模拟多用户同时向知识库提问，触发完整的 RAG 管线
"""

import random
from locust import task, between
from backend.tests.stress.conftest import StressUser, STRESS_QUESTIONS


class RAGStressUser(StressUser):
    """RAG 问答压测用户"""
    weight = 5  # 权重最高
    wait_time = between(3, 8)  # SSE 流式较慢，间隔放长

    def on_start(self):
        """每个用户登录并创建一个专属会话"""
        self.token, _ = self.login_as_new_user()
        self.conv_id = self.create_conversation(self.token)

    @task(10)
    def ask_question(self):
        """★ 核心：发送知识库问答（SSE 流式）"""
        question = random.choice(STRESS_QUESTIONS)
        self.send_rag_query(self.token, self.conv_id, question)

    @task(3)
    def list_conversations(self):
        """查看会话列表"""
        self.client.get("/api/chat/conversations", headers={
            "Authorization": f"Bearer {self.token}"
        })

    @task(1)
    def get_messages(self):
        """查看历史消息"""
        self.client.get(
            f"/api/chat/conversations/{self.conv_id}/messages",
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @task(1)
    def create_new_conversation(self):
        """偶尔创建新会话"""
        self.conv_id = self.create_conversation(self.token)


class AdminDocStressUser(StressUser):
    """管理员知识库压测（低频）"""
    weight = 1
    wait_time = between(5, 10)

    def on_start(self):
        self.token = self.get_admin_token()

    @task(3)
    def list_documents(self):
        self.client.get("/api/knowledge/documents", headers={
            "Authorization": f"Bearer {self.token}"
        })

    @task(1)
    def get_stats(self):
        self.client.get("/api/knowledge/stats", headers={
            "Authorization": f"Bearer {self.token}"
        })
