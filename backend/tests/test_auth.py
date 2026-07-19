"""认证模块测试"""

import pytest


class TestRegister:
    async def test_register_success(self, client):
        resp = await client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "pass123456",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data

    async def test_register_duplicate_username(self, client):
        await client.post("/api/auth/register", json={
            "username": "dup", "password": "pass123456"
        })
        resp = await client.post("/api/auth/register", json={
            "username": "dup", "password": "pass123456"
        })
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]

    async def test_register_short_password(self, client):
        resp = await client.post("/api/auth/register", json={
            "username": "test", "password": "1234567"  # 7位 < 8
        })
        assert resp.status_code == 422

    async def test_register_short_username(self, client):
        resp = await client.post("/api/auth/register", json={
            "username": "ab", "password": "pass123456"
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_login_admin_success(self, client):
        resp = await client.post("/api/auth/login", json={
            "username": "admin", "password": "123456"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        resp = await client.post("/api/auth/login", json={
            "username": "admin", "password": "wrong"
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/auth/login", json={
            "username": "nobody", "password": "123456"
        })
        assert resp.status_code == 401


class TestGetMe:
    async def test_get_me_with_token(self, client, admin_token):
        resp = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    async def test_get_me_without_token(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 403


class TestChangePassword:
    async def test_change_password_success(self, client, admin_token):
        resp = await client.post("/api/auth/change-password", json={
            "old_password": "123456",
            "new_password": "newpass123",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200

        # 验证新密码可登录
        resp2 = await client.post("/api/auth/login", json={
            "username": "admin", "password": "newpass123"
        })
        assert resp2.status_code == 200

    async def test_change_password_wrong_old(self, client, admin_token):
        resp = await client.post("/api/auth/change-password", json={
            "old_password": "wrongpass",
            "new_password": "newpass123",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 400


class TestPermission:
    async def test_user_cannot_access_admin(self, client, user_token):
        """普通用户不能访问知识库管理"""
        resp = await client.get("/api/knowledge/documents", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert resp.status_code == 403

    async def test_admin_can_access_knowledge(self, client, admin_token):
        resp = await client.get("/api/knowledge/documents", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert resp.status_code == 200
