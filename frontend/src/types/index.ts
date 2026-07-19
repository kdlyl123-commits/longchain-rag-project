// 用户类型
export interface User {
  id: number;
  username: string;
  email: string | null;
  role: "admin" | "user";
  is_active: boolean;
  created_at: string;
}

// 登录请求
export interface LoginRequest {
  username: string;
  password: string;
}

// 注册请求
export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
}

// 修改密码请求
export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

// 会话
export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

// 消息
export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

// 引用片段
export interface Citation {
  index?: number;
  doc_id?: number;
  chunk_id?: number;
  text: string;
  preview?: string;
  filename: string;
  score: number;
}

// 文档
export interface Document {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: "processing" | "done" | "error";
  chunk_count: number;
  created_at: string;
}

// 文档切片
export interface DocumentChunk {
  id: number;
  document_id: number;
  chunk_index: number;
  content: string;
  token_count: number;
}

// API 响应
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// 知识库统计
export interface KnowledgeStats {
  document_count: number;
  chunk_count: number;
  total_tokens: number;
}
