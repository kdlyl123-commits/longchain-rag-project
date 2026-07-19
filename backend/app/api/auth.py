from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ChangePasswordRequest,
    UserResponse,
)
from app.middleware.rate_limit import check_rate_limit
from app.services import auth_service
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    try:
        user = await auth_service.register_user(db, req.username, req.password, req.email)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """用户登录（含频率限制）"""
    await check_rate_limit(request)
    """用户登录"""
    try:
        user = await auth_service.authenticate_user(db, req.username, req.password)
        token = auth_service.create_access_token(user.id, user.username, user.role)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户信息"""
    from sqlalchemy import select
    from app.models.user import User
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    try:
        await auth_service.change_user_password(
            db, current_user["id"], req.old_password, req.new_password
        )
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
