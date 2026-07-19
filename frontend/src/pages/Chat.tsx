import { useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useChatStore } from "../stores/chatStore";
import ConversationList from "../components/ConversationList";
import ChatMessage from "../components/ChatMessage";
import ChatInput from "../components/ChatInput";
import { RobotOutlined } from "@ant-design/icons";

export default function Chat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const {
    messages,
    streamingContent,
    streaming,
    currentConversationId,
    fetchMessages,
    sendMessage,
    setCurrentConversation,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 当 URL 参数变化时，加载对应的消息
  useEffect(() => {
    if (conversationId) {
      const id = Number(conversationId);
      setCurrentConversation(id);
      fetchMessages(id);
    }
  }, [conversationId]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSend = async (content: string) => {
    const targetId = conversationId ? Number(conversationId) : currentConversationId;
    if (!targetId) {
      // 如果没有会话，先创建一个
      const { createConversation } = useChatStore.getState();
      const conv = await createConversation();
      navigate(`/chat/${conv.id}`);
      // 创建后递归发送
      return;
    }
    await sendMessage(content);
  };

  const hasMessages = messages.length > 0;

  return (
    <div style={{ display: "flex", height: "calc(100vh - 64px)" }}>
      {/* 左侧会话列表 */}
      <ConversationList />

      {/* 右侧对话区域 */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          background: "#fff",
        }}
      >
        {conversationId ? (
          <>
            {/* 消息列表 */}
            <div style={{ flex: 1, overflow: "auto" }}>
              {!hasMessages && !streaming ? (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    height: "100%",
                    color: "#bbb",
                  }}
                >
                  <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                  <p>开始提问吧！我会基于知识库为你解答</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))
              )}

              {/* 流式消息 */}
              {streaming && streamingContent && (
                <ChatMessage
                  message={{
                    id: 0,
                    conversation_id: Number(conversationId),
                    role: "assistant",
                    content: "",
                    citations: null,
                    created_at: "",
                  }}
                  streamingContent={streamingContent}
                />
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* 底部输入框 */}
            <ChatInput onSend={handleSend} disabled={streaming} />
          </>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "#bbb",
            }}
          >
            <RobotOutlined style={{ fontSize: 64, marginBottom: 16 }} />
            <h2 style={{ color: "#999", marginBottom: 8 }}>
              RAG 知识库问答系统
            </h2>
            <p>点击左侧"新建对话"开始提问</p>
          </div>
        )}
      </div>
    </div>
  );
}
