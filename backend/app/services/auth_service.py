from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.user import User

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


async def register_user(
    db: AsyncSession, username: str, password: str, email: str | None = None
) -> User:
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise ValueError("用户名已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        role="user",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise ValueError("用户名或密码错误")
    if not user.is_active:
        raise ValueError("账号已被禁用")

    return user


async def change_user_password(
    db: AsyncSession, user_id: int, old_password: str, new_password: str
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("用户不存在")
    if not verify_password(old_password, user.password_hash):
        raise ValueError("旧密码错误")

    user.password_hash = hash_password(new_password)
    await db.flush()


async def init_admin_user():
    """初始化管理员账号"""
    from app.database import async_session_factory

    async with async_session_factory() as db:
        result = await db.execute(
            select(User).where(User.username == settings.admin_username)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                role="admin",
                email="admin@example.com",
            )
            db.add(admin)
            await db.commit()
            print(f"[初始化] 管理员账号已创建: {settings.admin_username}")
        else:
            admin.role = "admin"
            admin.password_hash = hash_password(settings.admin_password)
            await db.commit()
