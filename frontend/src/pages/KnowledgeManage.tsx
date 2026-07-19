import { useEffect, useState } from "react";
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Popconfirm,
  Modal,
  Typography,
  message,
  Spin,
} from "antd";
import {
  DeleteOutlined,
  ReloadOutlined,
  EyeOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import DocumentUploader from "../components/DocumentUploader";
import { useKnowledgeStore } from "../stores/knowledgeStore";
import type { Document, DocumentChunk } from "../types";

const { Title, Paragraph } = Typography;

export default function KnowledgeManage() {
  const {
    documents,
    total,
    page,
    pageSize,
    stats,
    loading,
    fetchDocuments,
    deleteDocument,
    fetchChunks,
    reprocessDocument,
    fetchStats,
  } = useKnowledgeStore();

  const [chunkModalOpen, setChunkModalOpen] = useState(false);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);

  useEffect(() => {
    fetchDocuments();
    fetchStats();
  }, []);

  const handleViewChunks = async (docId: number) => {
    setChunkModalOpen(true);
    setChunksLoading(true);
    try {
      const result = await fetchChunks(docId);
      setChunks(result);
    } catch {
      // error handled in interceptor
    } finally {
      setChunksLoading(false);
    }
  };

  const fileSizeFormat = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const columns: ColumnsType<Document> = [
    {
      title: "文件名",
      dataIndex: "filename",
      key: "filename",
      ellipsis: true,
    },
    {
      title: "类型",
      dataIndex: "file_type",
      key: "file_type",
      width: 80,
      render: (t: string) => <Tag>{t.toUpperCase()}</Tag>,
    },
    {
      title: "大小",
      dataIndex: "file_size",
      key: "file_size",
      width: 100,
      render: (s: number) => fileSizeFormat(s),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          processing: "processing",
          done: "success",
          error: "error",
        };
        const labelMap: Record<string, string> = {
          processing: "处理中",
          done: "已完成",
          error: "失败",
        };
        return <Tag color={colorMap[status]}>{labelMap[status]}</Tag>;
      },
    },
    {
      title: "切片数",
      dataIndex: "chunk_count",
      key: "chunk_count",
      width: 80,
    },
    {
      title: "上传时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (t: string) => new Date(t).toLocaleString("zh-CN"),
    },
    {
      title: "操作",
      key: "actions",
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewChunks(record.id)}
          >
            切片
          </Button>
          {record.status === "error" && (
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              onClick={async () => {
                await reprocessDocument(record.id);
                fetchDocuments();
              }}
            >
              重试
            </Button>
          )}
          <Popconfirm
            title="确认删除"
            description="删除后数据和向量将无法恢复"
            onConfirm={async () => {
              await deleteDocument(record.id);
              message.success("已删除");
            }}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: "0 auto" }}>
      {/* 统计卡片 */}
      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <Card size="small" style={{ flex: 1 }}>
          <Title level={4} style={{ margin: 0 }}>
            {stats?.document_count ?? 0}
          </Title>
          <span style={{ color: "#888" }}>文档总数</span>
        </Card>
        <Card size="small" style={{ flex: 1 }}>
          <Title level={4} style={{ margin: 0 }}>
            {stats?.chunk_count ?? 0}
          </Title>
          <span style={{ color: "#888" }}>切片总数</span>
        </Card>
        <Card size="small" style={{ flex: 1 }}>
          <Title level={4} style={{ margin: 0 }}>
            {(stats?.total_tokens ?? 0).toLocaleString()}
          </Title>
          <span style={{ color: "#888" }}>总 Token 数</span>
        </Card>
      </div>

      {/* 上传区域 */}
      <Card style={{ marginBottom: 24 }}>
        <DocumentUploader onSuccess={() => fetchDocuments()} />
      </Card>

      {/* 文档列表 */}
      <Card title="文档列表">
        <Table
          columns={columns}
          dataSource={documents}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p) => fetchDocuments(p),
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </Card>

      {/* 切片预览弹窗 */}
      <Modal
        title="文档切片预览"
        open={chunkModalOpen}
        onCancel={() => setChunkModalOpen(false)}
        width={800}
        footer={null}
      >
        {chunksLoading ? (
          <Spin />
        ) : (
          <div style={{ maxHeight: 500, overflow: "auto" }}>
            {chunks.map((chunk) => (
              <Card
                key={chunk.id}
                size="small"
                style={{ marginBottom: 8 }}
                title={`片段 #${chunk.chunk_index + 1}（约 ${chunk.token_count} Token）`}
              >
                <Paragraph
                  ellipsis={{ rows: 3, expandable: true, symbol: "展开" }}
                >
                  {chunk.content}
                </Paragraph>
              </Card>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
}
