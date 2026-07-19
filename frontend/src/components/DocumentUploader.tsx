import { useState } from "react";
import { Upload, Button, message } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import type { UploadProps } from "antd";
import { useKnowledgeStore } from "../stores/knowledgeStore";

const { Dragger } = Upload;

export default function DocumentUploader({
  onSuccess,
}: {
  onSuccess: () => void;
}) {
  const [uploading, setUploading] = useState(false);
  const { uploadDocument } = useKnowledgeStore();

  const props: UploadProps = {
    name: "file",
    multiple: false,
    accept: ".pdf,.docx,.doc,.txt,.md,.csv",
    showUploadList: false,
    beforeUpload: async (file) => {
      const allowedTypes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/markdown",
        "text/csv",
      ];
      const ext = file.name.split(".").pop()?.toLowerCase();
      const allowedExts = ["pdf", "docx", "doc", "txt", "md", "csv"];

      if (!ext || !allowedExts.includes(ext)) {
        message.error(`不支持的文件类型: ${ext}`);
        return false;
      }

      if (file.size > 50 * 1024 * 1024) {
        message.error("文件大小不能超过 50MB");
        return false;
      }

      setUploading(true);
      try {
        await uploadDocument(file);
        message.success(`"${file.name}" 上传成功，正在处理中...`);
        onSuccess();
      } catch {
        // 错误已在拦截器中处理
      } finally {
        setUploading(false);
      }
      return false; // 阻止默认上传行为
    },
  };

  return (
    <Dragger {...props} disabled={uploading}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">
        点击或拖拽文件到此区域上传
      </p>
      <p className="ant-upload-hint">
        支持 PDF、Word、TXT、Markdown、CSV 格式，单个文件不超过 50MB
      </p>
    </Dragger>
  );
}
