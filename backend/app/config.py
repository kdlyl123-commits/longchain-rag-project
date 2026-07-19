from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 运行模式
    storage_mode: str = "local"  # "local" | "minio"

    # 百炼 API
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # LLM 模型
    llm_model: str = "qwen-plus"
    llm_model_simple: str = "qwen-turbo"
    llm_model_complex: str = "qwen-max"

    # Embedding
    embedding_model: str = "text-embedding-v4"
    embedding_dimensions: int = 1024

    # Rerank
    rerank_model: str = "qwen3-rerank"

    # 数据库（sqlite 用本地，postgresql 用 Docker）
    database_url: str = "sqlite+aiosqlite:///./rag_ecommerce.db"
    database_url_sync: str = "sqlite:///./rag_ecommerce.db"

    # Redis（空着=内存缓存）
    redis_url: str = ""

    # Chroma（host 空着=嵌入式模式）
    chroma_host: str = ""
    chroma_port: int = 8001

    # MinIO（STORAGE_MODE=local 时用本地文件）
    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "knowledge-base"

    # JWT（生产环境必须通过环境变量设置强密钥）
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # 管理员（仅首次启动时使用，之后修改密码不受影响）
    admin_username: str = "admin"
    admin_password: str = ""

    # 应用
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # 上传
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
