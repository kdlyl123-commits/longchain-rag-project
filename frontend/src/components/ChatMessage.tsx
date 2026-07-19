import { useState } from "react";
import { Typography, Tag, Button } from "antd";
import {
  UserOutlined,
  RobotOutlined,
  DownOutlined,
  UpOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import type { Message, Citation } from "../types";

const { Text } = Typography;

function CitationCard({ cite }: { cite: Citation }) {
  const [expanded, setExpanded] = useState(false);
  const preview = cite.preview || cite.text.slice(0, 50);
  const hasMore = cite.text.length > preview.length;

  return (
    <div
      style={{
        padding: "8px 12px",
        background: "#f0f5ff",
        border: "1px solid #d6e4ff",
        borderRadius: 6,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 4,
        }}
      >
        <Text strong style={{ fontSize: 13, color: "#1677ff" }}>
          [{cite.index}] {cite.filename}
        </Text>
        <Tag color={cite.score > 70 ? "green" : cite.score > 40 ? "blue" : "default"}>
          相关度 {cite.score}%
        </Tag>
      </div>
      <div
        style={{
          fontSize: 13,
          color: "#555",
          whiteSpace: "pre-wrap",
        }}
      >
        {expanded ? cite.text : preview}
      </div>
      {hasMore && (
        <Button
          type="link"
          size="small"
          icon={expanded ? <UpOutlined /> : <DownOutlined />}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "收起" : "展开"}
        </Button>
      )}
    </div>
  );
}

interface Props {
  message: Message;
  streamingContent?: string;
}

export default function ChatMessage({ message, streamingContent }: Props) {
  const isUser = message.role === "user";
  const displayContent = streamingContent ?? message.content;
  const citations = message.citations as Citation[] | null;

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        padding: "16px 24px",
        background: isUser ? "#fff" : "#f7f8fa",
        borderBottom: "1px solid #f0f0f0",
      }}
    >
      {/* 头像 */}
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          background: isUser ? "#1677ff" : "#52c41a",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
          flexShrink: 0,
        }}
      >
        {isUser ? <UserOutlined /> : <RobotOutlined />}
      </div>

      {/* 消息内容 */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        <div style={{ marginBottom: 4 }}>
          <Text strong style={{ fontSize: 13 }}>
            {isUser ? "你" : "AI 助手"}
          </Text>
        </div>

        {isUser ? (
          <div style={{ whiteSpace: "pre-wrap", fontSize: 14 }}>
            {displayContent}
          </div>
        ) : (
          <div className="markdown-body" style={{ fontSize: 14 }}>
            <ReactMarkdown rehypePlugins={[rehypeSanitize]} remarkPlugins={[remarkGfm]}>
              {displayContent}
            </ReactMarkdown>
          </div>
        )}

        {/* 引用展示 */}
        {!isUser && citations && citations.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div
              style={{
                borderLeft: "3px solid #1677ff",
                paddingLeft: 10,
                marginBottom: 8,
              }}
            >
              <Text strong style={{ fontSize: 13, color: "#1677ff" }}>
                📎 引用来源（{citations.length}条）
              </Text>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {citations.map((cite, i) => (
                <CitationCard key={i} cite={cite} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
