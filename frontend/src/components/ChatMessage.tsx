import { useState } from "react";
import { Typography, Tag, Collapse } from "antd";
import {
  UserOutlined,
  RobotOutlined,
  LinkOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import type { Message, Citation } from "../types";

const { Text } = Typography;

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
            <ReactMarkdown>{displayContent}</ReactMarkdown>
          </div>
        )}

        {/* 引用展示 */}
        {!isUser && citations && citations.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Collapse
              size="small"
              ghost
              items={[
                {
                  key: "citations",
                  label: (
                    <span style={{ fontSize: 12, color: "#888" }}>
                      <LinkOutlined /> 引用来源（{citations.length}）
                    </span>
                  ),
                  children: (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {citations.map((cite, i) => (
                        <div
                          key={i}
                          style={{
                            padding: 8,
                            background: "#fff",
                            border: "1px solid #e8e8e8",
                            borderRadius: 6,
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              marginBottom: 4,
                            }}
                          >
                            <Text strong style={{ fontSize: 12 }}>
                              [{cite.index || i + 1}] {cite.filename}
                            </Text>
                            <Tag color="blue" style={{ fontSize: 10 }}>
                              相似度: {(cite.score * 100).toFixed(1)}%
                            </Tag>
                          </div>
                          <Text
                            type="secondary"
                            style={{ fontSize: 12 }}
                            ellipsis={{ rows: 2 } as any}
                          >
                            {cite.text}
                          </Text>
                        </div>
                      ))}
                    </div>
                  ),
                },
              ]}
            />
          </div>
        )}
      </div>
    </div>
  );
}
