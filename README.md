# 📚 RAG 企业级知识库问答系统

基于 **LangChain + 阿里云百炼 API** 的电商商品知识库问答系统。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design 5 + Vite |
| 后端 | FastAPI + LangChain + Celery |
| LLM | 阿里云百炼 (qwen-plus / qwen-max / qwen-turbo) |
| Embedding | 百炼 text-embedding-v4 |
| Rerank | 百炼 qwen3-rerank |
| 向量库 | Chroma |
| 数据库 | PostgreSQL + Redis |
| 存储 | MinIO |
| 部署 | Docker Compose |

## 快速开始

### 前置条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 已安装并运行
- 阿里云百炼 API Key（`.env` 文件已配置好）

### 1. 启动所有服务

打开终端，进入项目目录：

```bash
cd "D:\longchain rag project"
docker compose up -d
```

首次启动会拉取镜像并构建，大概需要 3-5 分钟。

### 2. 查看启动状态

```bash
docker compose ps
```

看到所有服务都是 `healthy` 或 `running` 就说明启动成功了。

### 3. 访问系统

| 地址 | 用途 |
|------|------|
| http://localhost:3000 | 前端界面 |
| http://localhost:8000/docs | 后端 API 文档 (Swagger) |
| http://localhost:9001 | MinIO 控制台 (minioadmin/minioadmin) |

### 4. 登录

- 管理员：`admin` / `123456`（可管理知识库 + 问答）
- 注册新用户：点击登录页的"立即注册"（只能问答）

## 使用流程

### 管理员上传知识库文档

1. 用 admin 登录，点击顶部 **"知识库管理"**
2. 拖拽或点击上传文档（支持 PDF、Word、TXT、Markdown、CSV）
3. 等待状态变为 **"已完成"**（Celery 异步处理，几秒到几分钟取决于文档大小）
4. 文档向量化后即可在问答中被检索到

### 用户问答

1. 点击左侧 **"新建对话"**
2. 输入问题，按 Enter 发送
3. AI 基于知识库回答，底部可展开查看**引用来源**
4. 对话历史自动保存，左侧可随时切换

## 常用命令

```bash
# 启动
docker compose up -d

# 查看日志
docker compose logs -f backend

# 重启某个服务
docker compose restart backend

# 停止所有服务
docker compose down

# 停止并删除数据（重新开始）
docker compose down -v
```

## 项目结构

```
├── docker-compose.yml       # 一键编排所有服务
├── .env                     # 百炼 API Key 等配置
├── .env.example             # 配置模板
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置管理
│   │   ├── api/             # 路由 (auth/chat/knowledge)
│   │   ├── models/          # 数据库模型
│   │   ├── schemas/         # Pydantic 模型
│   │   ├── services/        # 业务逻辑
│   │   ├── rag/             # LangChain 模块
│   │   ├── middleware/      # JWT + 限流
│   │   └── utils/           # 缓存工具
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/           # 页面 (Login/Chat/Knowledge等)
│       ├── components/      # 组件 (消息/会话列表等)
│       ├── stores/          # Zustand 状态
│       └── api/             # API 请求
└── nginx/
    └── default.conf
```

## 本地开发（不使用 Docker）

如果你不想用 Docker，需要本地安装并运行 PostgreSQL、Redis、Chroma、MinIO，然后：

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```
