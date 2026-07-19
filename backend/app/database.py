from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# 判断数据库类型
_use_sqlite = "sqlite" in settings.database_url

if _use_sqlite:
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,  # 写锁等待最长 30 秒
        },
    )
    # 开启 WAL 模式提升并发读写性能
    from sqlalchemy import event
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.close()
else:
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )

# 同步引擎（Celery / init_admin 用）
from sqlalchemy import create_engine
if _use_sqlite:
    sync_engine = create_engine(
        settings.database_url_sync,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    sync_engine = create_engine(
        settings.database_url_sync,
        echo=False,
        pool_size=10,
        max_overflow=5,
        pool_pre_ping=True,
    )

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖：获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
