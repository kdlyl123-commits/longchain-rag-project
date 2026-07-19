"""RAG 服务层：处理问答请求"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.conversation import Conversation
from app.models.message import Message
from app.rag.chain import stream_rag_response


async def process_query(
    db: AsyncSession,
    user_id: int,
    conversation_id: int,
    query: str,
) -> tuple:
    """处理用户提问：保存消息 + 构建 RAG 上下文"""
    # 获取对话历史
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(10)
    )
    history = result.scalars().all()

    # 保存用户消息
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=query,
    )
    db.add(user_msg)

    # 更新会话标题（使用第一条消息的前 30 字）
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.role == "user")
    )
    msg_count = len(result.scalars().all())
    if msg_count <= 1:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if conv:
            conv.title = query[:30] + ("..." if len(query) > 30 else "")

    await db.flush()

    # 构建历史消息
    history_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]

    return history_messages, user_msg.id
