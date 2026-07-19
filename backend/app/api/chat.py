"""对话 API 路由"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.chat import (
    QueryRequest,
    CreateConversationRequest,
    ConversationResponse,
    MessageResponse,
)
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.rag_service import process_query
from app.rag.chain import stream_rag_response

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有会话"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user["id"])
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return conversations


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    req: CreateConversationRequest | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新会话"""
    conv = Conversation(
        user_id=current_user["id"],
        title=req.title if req and req.title else "新对话",
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除会话（只能删除自己的会话）"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if conv.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="无权限删除该会话")

    await db.delete(conv)
    await db.flush()
    return {"message": "会话已删除"}


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会话历史消息"""
    # 验证会话所有权
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv or conv.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="会话不存在")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return messages


@router.post("/conversations/{conversation_id}/query")
async def query_knowledge_base(
    conversation_id: int,
    req: QueryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """向知识库提问（SSE 流式返回）"""
    # 验证会话所有权
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv or conv.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 处理查询
    history_messages, user_msg_id = await process_query(
        db, current_user["id"], conversation_id, req.content
    )

    async def generate():
        full_response = ""
        citations_data = None

        try:
            async for chunk in stream_rag_response(req.content, history_messages):
                # 解析引用数据
                if chunk.startswith("data: ") and '"type": "citations"' in chunk:
                    try:
                        data = json.loads(chunk[6:].strip())
                        citations_data = data.get("citations")
                    except json.JSONDecodeError:
                        pass
                    yield chunk
                elif chunk.startswith("data: ") and '"type": "content"' in chunk:
                    try:
                        data = json.loads(chunk[6:].strip())
                        full_response += data.get("content", "")
                    except json.JSONDecodeError:
                        pass
                    yield chunk
                else:
                    yield chunk
        finally:
            # SSE 结束后保存 AI 回复
            if full_response:
                from app.database import async_session_factory
                async with async_session_factory() as save_db:
                    assistant_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_response,
                        citations=citations_data,
                    )
                    save_db.add(assistant_msg)
                    await save_db.commit()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
