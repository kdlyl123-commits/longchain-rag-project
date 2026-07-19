from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理"""
    # 安全检查：密钥不能为空
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY 未设置，请在 .env 中配置一个强随机密钥")
    if not settings.admin_password:
        raise RuntimeError("ADMIN_PASSWORD 未设置，请在 .env 中配置管理员密码")

    await init_db()
    from app.services.auth_service import init_admin_user
    await init_admin_user()
    from app.services.document_service import ensure_storage
    ensure_storage()
    yield


app = FastAPI(
    title="RAG 企业级知识库问答系统",
    description="基于 LangChain + 阿里云百炼 API 的电商商品知识库问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

from app.api import auth, chat, knowledge
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "rag-ecommerce"}
