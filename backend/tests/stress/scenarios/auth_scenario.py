"""
场景 A：认证压测
模拟大量用户注册 + 登录 + 获取个人信息
"""

import random
from locust import task, between
from backend.tests.stress.conftest import StressUser, random_username, random_password


class AuthStressUser(StressUser):
    """认证压测用户"""
    weight = 3  # 权重
    wait_time = between(2, 5)  # 每轮操作间隔 2-5 秒

    def on_start(self):
        """每个虚拟用户启动时执行一次"""
        self.token, self.username = self.login_as_new_user()

    @task(5)
    def get_me(self):
        """高频：获取个人信息"""
        self.client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {self.token}"
        })

    @task(2)
    def login_again(self):
        """中频：重新登录"""
        self.client.post("/api/auth/login", json={
            "username": self.username,
            "password": random_password(),  # 用错密码，测试错误处理
        })

    @task(1)
    def change_password(self):
        """低频：修改密码"""
        new_pwd = random_password()
        self.client.post("/api/auth/change-password", json={
            "old_password": "TestPass123!",
            "new_password": new_pwd,
        }, headers={"Authorization": f"Bearer {self.token}"})

    @task(3)
    def register_new_user(self):
        """中频：注册新用户"""
        self.client.post("/api/auth/register", json={
            "username": random_username(),
            "password": random_password(),
        })
