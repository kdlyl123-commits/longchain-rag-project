import { useEffect } from "react";
import { List, Button, Typography, Popconfirm, Spin } from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  MessageOutlined,
} from "@ant-design/icons";
import { useChatStore } from "../stores/chatStore";
import { useNavigate, useParams } from "react-router-dom";

const { Text } = Typography;

export default function ConversationList() {
  const {
    conversations,
    currentConversationId,
    loading,
    fetchConversations,
    createConversation,
    deleteConversation,
  } = useChatStore();
  const navigate = useNavigate();
  const { conversationId } = useParams();

  useEffect(() => {
    fetchConversations();
  }, []);

  const handleNewConversation = async () => {
    const conv = await createConversation();
    navigate(`/chat/${conv.id}`);
  };

  const handleSelect = (id: number) => {
    navigate(`/chat/${id}`);
  };

  return (
    <div
      style={{
        width: 280,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        borderRight: "1px solid #f0f0f0",
        background: "#fafafa",
      }}
    >
      <div style={{ padding: "12px 16px" }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={handleNewConversation}
        >
          新建对话
        </Button>
      </div>

      <div style={{ flex: 1, overflow: "auto" }}>
        {loading && conversations.length === 0 ? (
          <div style={{ textAlign: "center", padding: 24 }}>
            <Spin />
          </div>
        ) : (
          <List
            dataSource={conversations}
            renderItem={(item) => {
              const isActive = item.id === (conversationId ? Number(conversationId) : currentConversationId);
              return (
                <div
                  onClick={() => handleSelect(item.id)}
                  style={{
                    padding: "10px 16px",
                    cursor: "pointer",
                    background: isActive ? "#e6f4ff" : "transparent",
                    borderLeft: isActive ? "3px solid #1677ff" : "3px solid transparent",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = isActive
                      ? "#e6f4ff"
                      : "#f0f0f0")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = isActive
                      ? "#e6f4ff"
                      : "transparent")
                  }
                >
                  <div style={{ flex: 1, overflow: "hidden" }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                      }}
                    >
                      <MessageOutlined
                        style={{ fontSize: 12, color: "#999" }}
                      />
                      <Text
                        ellipsis
                        style={{
                          fontSize: 13,
                          maxWidth: 180,
                        }}
                      >
                        {item.title}
                      </Text>
                    </div>
                    <Text
                      type="secondary"
                      style={{ fontSize: 11, marginLeft: 18 }}
                    >
                      {new Date(item.updated_at).toLocaleDateString("zh-CN")}
                    </Text>
                  </div>
                  <Popconfirm
                    title="确认删除该会话？"
                    onConfirm={(e) => {
                      e?.stopPropagation();
                      deleteConversation(item.id);
                    }}
                    onCancel={(e) => e?.stopPropagation()}
                  >
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Popconfirm>
                </div>
              );
            }}
          />
        )}
      </div>
    </div>
  );
}
