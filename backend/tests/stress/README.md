# RAG 系统压力测试方案

## 一、工具选择：Locust

选 Locust 而不是 JMeter/k6/wrk，原因是：
- **Python 原生**，和你的后端同语言，写压测脚本零学习成本
- **原生支持 SSE**——你的 RAG 问答是流式返回的，这是其他工具做不到的
- **自带 Web UI**，打开浏览器就能实时看图表

## 二、压测三个场景

| 场景 | 测什么 | 怎么测 |
|------|--------|--------|
| **A 认证** | JWT 生成、DB 写入 | 50 个用户循环注册→登录→查个人信息 |
| **B RAG问答** ★ | Embedding、检索、LLM 流式生成、SSE | 10→50→100 用户逐步加码，持续发问题 |
| **C 混合负载** | 真实用户行为 | 70%浏览 + 20%频繁提问 + 10%管理员上传 |

## 三、四个压力等级

| 等级 | 并发 | 时长 | 目的 |
|------|:---:|------|------|
| 🟢 轻量 | 10 | 2 分钟 | 先确认系统不崩 |
| 🟡 中等 | 50 | 5 分钟 | 找出性能拐点 |
| 🟠 重度 | 100 | 10 分钟 | 找出极限值 |
| 🔴 极限 | 200+ | 15 分钟 | 观察怎么崩的 |

## 四、七个关键指标

| 指标 | 含义 | 及格 | 优秀 |
|------|------|:---:|:---:|
| RPS | 每秒处理多少请求 | >20 | >100 |
| P50 延迟 | 一半请求多久响应 | <500ms | <200ms |
| P95 延迟 | 95% 请求多久响应 | <2s | <1s |
| 错误率 | 失败占比 | <1% | <0.1% |
| SSE 首字节 | 回答第一个字要多久 | <3s | <1s |
| CPU | 压测时 CPU 占用 | <80% | <50% |
| 内存 | 会不会越用越多 | 不涨 | 不涨 |

## 五、API Token 保护

RAG 问答场景默认走**干跑模式**（`dry_run=true`）——后端跳过 Embedding 和 LLM API 调用，用模拟数据替代。压测的是 HTTP、数据库、SSE 流式这些真正可能成为瓶颈的部分，**不花你一分钱 Token**。

如果想测真实 RAG 管线的性能，把 `conftest.py` 里 `send_rag_query` 的 `dry_run` 改为 `False`（**注意会消耗 API 额度**）。

## 六、如何运行

### 1. 安装 Locust

```bash
pip install locust
```

### 2. 确保后端在运行

```bash
# 注意：必须在 backend 目录下运行
cd "D:\longchain rag project\backend"
python -m uvicorn app.main:app --port 8000
```

### 3. 启动压测（另开一个终端）

```bash
# 注意：必须在 stress 目录下运行
cd "D:\longchain rag project\backend\tests\stress"
```

**三种场景，选一个跑：**

```bash
# 场景A：认证压测（注册、登录、个人信息）
python -m locust -f locustfile_auth.py --host=http://localhost:8000

# 场景B：RAG 问答压测（SSE 流式问答、会话管理）★ 核心
python -m locust -f locustfile_rag.py --host=http://localhost:8000

# 场景C：管理员知识库压测（文档列表、统计）
python -m locust -f locustfile_admin.py --host=http://localhost:8000

# 或者三合一（全部场景一起跑）
python -m locust -f locustfile.py --host=http://localhost:8000
```

### 4. 打开 Web UI

浏览器访问 **http://localhost:8089**，设置用户数和增长速率，点击 Start。

### 5. 无界面模式（命令行直接跑）

```bash
# 认证压测：20 用户，5 人/秒增长，跑 30 秒
python -m locust -f locustfile_auth.py --host=http://localhost:8000 --headless -u 20 -r 5 -t 30s

# RAG 压测：10 用户（省 Token），2 人/秒，跑 60 秒
python -m locust -f locustfile_rag.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s

# 管理员压测：5 用户，1 人/秒，跑 30 秒
python -m locust -f locustfile_admin.py --host=http://localhost:8000 --headless -u 5 -r 1 -t 30s
```

参数说明：`-u 20` 总用户数、`-r 5` 每秒新增用户数、`-t 30s` 持续 30 秒

## 七、压测脚本

```
stress/
├── README.md                # 本文件
├── locustfile.py            # 主入口，Locust 自动发现 HttpUser 子类
├── conftest.py              # 共享工具（登录、创建会话、发RAG查询）
└── scenarios/
    ├── auth_scenario.py     # 场景A：认证压测
    └── rag_scenario.py      # 场景B：RAG问答 + 管理员文档浏览
```

## 八、压测后输出

Locust Web UI 自动生成：
- 请求统计表（RPS、延迟分布、错误率）
- 响应时间曲线图
- 用户数增长曲线
- 失败/异常详情
