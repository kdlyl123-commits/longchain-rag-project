"""共享测试夹具"""

import os
import sys
import pytest
from httpx import ASGITransport, AsyncClient

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 强制使用测试配置
os.environ["STORAGE_MODE"] = "local"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./test.db"
os.environ["CHROMA_HOST"] = ""
os.environ["REDIS_URL"] = ""
os.environ["MINIO_ENDPOINT"] = ""
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "123456"

from app.main import app
from app.database import Base, async_session_factory, engine
from app.models import User, Conversation, Message, Document, DocumentChunk
from app.services.auth_service import hash_password


@pytest.fixture(autouse=True)
async def setup_db():
    """每个测试前重建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 创建管理员
    async with async_session_factory() as db:
        from sqlalchemy import select
        admin = User(
            username="admin",
            password_hash=hash_password("123456"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()

    yield

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """异步 HTTP 测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_token(client):
    """获取管理员 Token"""
    resp = await client.post("/api/auth/login", json={
        "username": "admin", "password": "123456"
    })
    data = resp.json()
    return data["access_token"]


@pytest.fixture
async def user_token(client):
    """获取普通用户 Token（先注册再登录）"""
    await client.post("/api/auth/register", json={
        "username": "testuser",
        "password": "testpass123",
    })
    resp = await client.post("/api/auth/login", json={
        "username": "testuser", "password": "testpass123"
    })
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    """管理员请求头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token):
    """普通用户请求头"""
    return {"Authorization": f"Bearer {user_token}"}


# 清理测试数据库文件
def pytest_sessionfinish(session, exitstatus):
    import os
    test_db = os.path.join(os.path.dirname(__file__), "..", "test.db")
    if os.path.exists(test_db):
        os.remove(test_db)
