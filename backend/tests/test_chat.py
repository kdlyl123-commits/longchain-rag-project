"""对话模块测试"""

import pytest


class TestConversations:
    async def test_create_conversation(self, client, user_headers):
        resp = await client.post("/api/chat/conversations", json={
            "title": "测试对话"
        }, headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "测试对话"
        assert "id" in data

    async def test_create_conversation_default_title(self, client, user_headers):
        resp = await client.post("/api/chat/conversations", json={}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "新对话"

    async def test_list_conversations_empty(self, client, user_headers):
        resp = await client.get("/api/chat/conversations", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_conversations(self, client, user_headers):
        await client.post("/api/chat/conversations", json={"title": "A"}, headers=user_headers)
        await client.post("/api/chat/conversations", json={"title": "B"}, headers=user_headers)
        resp = await client.get("/api/chat/conversations", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    async def test_delete_conversation(self, client, user_headers):
        resp = await client.post("/api/chat/conversations", json={}, headers=user_headers)
        conv_id = resp.json()["id"]
        resp2 = await client.delete(f"/api/chat/conversations/{conv_id}", headers=user_headers)
        assert resp2.status_code == 200

        # 确认已删除
        resp3 = await client.get("/api/chat/conversations", headers=user_headers)
        assert resp3.json() == []

    async def test_cannot_delete_others_conversation(self, client, user_headers, admin_token):
        """用户A不能删除用户B的会话"""
        # admin 创建一个会话
        resp = await client.post("/api/chat/conversations", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        conv_id = resp.json()["id"]
        # 普通用户尝试删除 → 会话存在但不属于当前用户
        resp2 = await client.delete(f"/api/chat/conversations/{conv_id}", headers=user_headers)
        # 404=不存在, 403=无权限, 两种都合理
        assert resp2.status_code in (403, 404)

    async def test_conversations_isolated_by_user(self, client, user_headers, admin_token):
        """每个用户只能看到自己的会话"""
        await client.post("/api/chat/conversations", json={"title": "User"}, headers=user_headers)
        await client.post("/api/chat/conversations", json={"title": "Admin"}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        resp = await client.get("/api/chat/conversations", headers=user_headers)
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "User"


class TestMessages:
    @pytest.fixture
    async def conversation(self, client, user_headers):
        resp = await client.post("/api/chat/conversations", json={
            "title": "Test"
        }, headers=user_headers)
        return resp.json()["id"]

    async def test_get_messages_empty(self, client, user_headers, conversation):
        resp = await client.get(
            f"/api/chat/conversations/{conversation}/messages",
            headers=user_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_cannot_access_others_messages(self, client, user_headers, admin_token):
        """不能访问别人的会话消息"""
        # admin 创建会话
        resp = await client.post("/api/chat/conversations", json={}, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        conv_id = resp.json()["id"]
        # 普通用户尝试访问
        resp2 = await client.get(
            f"/api/chat/conversations/{conv_id}/messages",
            headers=user_headers
        )
        assert resp2.status_code == 404
