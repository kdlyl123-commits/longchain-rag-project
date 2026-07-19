"""
压测共享工具：
- 登录获取 Token
- 创建会话
- 管理员 Token 缓存
- 自动重试（应对高并发下服务偶尔拒绝）
"""

import random
import string
import time
from locust import HttpUser

STRESS_QUESTIONS = [
    "身高178cm，体重135斤，推荐什么尺码？",
    "这件衣服怎么洗？可以机洗吗？",
    "这个商品支持七天无理由退货吗？",
    "有优惠券可以用吗？",
    "发货用什么快递？多久能到？",
    "这款商品有别的颜色吗？",
    "面料是什么材质的？",
    "和另一款相比哪个更好？",
]


def random_username():
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"st_{suffix}"


def random_password():
    return "TestPass123!"


class StressUser(HttpUser):
    """压测用户基类，带自动重试"""

    _admin_token: str | None = None

    def _post_json(self, path, json_data, headers=None, max_retries=3):
        """发送 POST 请求，自动重试空响应"""
        for attempt in range(max_retries):
            resp = self.client.post(path, json=json_data, headers=headers)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if data:
                        return resp
                except Exception:
                    pass
            # 服务器繁忙，等一会儿重试
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
        return resp

    def login(self, username: str = "admin", password: str = "123456") -> str:
        resp = self._post_json("/api/auth/login", {
            "username": username, "password": password,
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        # 注册后再登录
        self._post_json("/api/auth/register", {
            "username": username, "password": password,
        })
        resp = self._post_json("/api/auth/login", {
            "username": username, "password": password,
        })
        return resp.json()["access_token"]

    def login_as_new_user(self) -> tuple[str, str]:
        username = random_username()
        password = random_password()
        self._post_json("/api/auth/register", {
            "username": username, "password": password,
        })
        resp = self._post_json("/api/auth/login", {
            "username": username, "password": password,
        })
        return resp.json()["access_token"], username

    def get_admin_token(self) -> str:
        """获取管理员 Token（类级缓存，只登录一次）"""
        if StressUser._admin_token is None:
            StressUser._admin_token = self.login("admin", "123456")
        return StressUser._admin_token

    def create_conversation(self, token: str) -> int:
        resp = self._post_json("/api/chat/conversations",
            {"title": "压测对话"},
            headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            return resp.json().get("id", 0)
        return 0

    def send_rag_query(self, token: str, conversation_id: int, question: str, dry_run: bool = True):
        """
        发送 RAG 问答请求（SSE 流式）

        dry_run=True: 干跑模式，不消耗 Embedding/LLM API Token
        dry_run=False: 真实模式，消耗 API Token
        """
        with self.client.post(
            f"/api/chat/conversations/{conversation_id}/query",
            json={"content": question, "dry_run": dry_run},
            headers={"Authorization": f"Bearer {token}"},
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Query failed: {resp.status_code} {resp.text[:100]}")
