# Memory Provider 侧车（memory-tencentdb）

> Hermes 的 TencentDB Agent Memory 系统（L0 对话捕获 → L1 事件提取 → L2 场景块 → L3 人格合成）依赖一个 Node.js Gateway sidecar 进程。主文件见 `SKILL.md` 任务路由 E。

## 架构

```
Hermes Agent (Python)
  └─ plugins/memory/memory_tencentdb/   ← 提供者（HTTP 客户端 + 进程 supervisor）
       │  启动 /health 检查
       ▼  HTTP (127.0.0.1:8420)
  memory-tencentdb Gateway (Node.js)     ← 侧车
       └─ L0~L3 存储 (SQLite + sqlite-vec)
```

**网关位置：** `~/.hermes/plugins/tdai-memory-openclaw-plugin/` — 由提供者自动发现并启动。

## 6.1 ⚠️ LLM 凭证配置（关键陷阱）

**Gateway 读的是 `TDAI_LLM_*` 环境变量，不是 `MEMORY_TENCENTDB_LLM_*`。**

```yaml
# ~/.memory-tencentdb/memory-tdai/tdai-gateway.yaml
# 注入到 data dir 里的 YAML 配置文件，Gateway 启动时自动读取
server:
  host: "127.0.0.1"
  port: 8420

llm:
  baseUrl: "https://api.deepseek.com"  # 默认 https://api.openai.com/v1
  model: "deepseek-v4-flash"           # 默认 gpt-4o
  apiKey: ***                     # 默认空字符串 → 调 OpenAI
```

环境变量备选（YAML 文件比 env var 优先级高）：

```bash
export TDAI_LLM_API_KEY="sk-..."
export TDAI_LLM_BASE_URL="https://api.deepseek.com"
export TDAI_LLM_MODEL="deepseek-v4-flash"
```

**Env var 名字对照表：**

| 提供者读取 (provider 转发) | Gateway 读取 | 说明 |
|---|---|---|
| `MEMORY_TENCENTDB_LLM_API_KEY` | `TDAI_LLM_API_KEY` | 必须设置，否则走 OpenAI 默认 |
| `MEMORY_TENCENTDB_LLM_BASE_URL` | `TDAI_LLM_BASE_URL` | 默认 `https://api.openai.com/v1` |
| `MEMORY_TENCENTDB_LLM_MODEL` | `TDAI_LLM_MODEL` | 默认 `gpt-4o` |
| — | `TDAI_LLM_MAX_TOKENS` | 默认 4096 |
| — | `TDAI_LLM_TIMEOUT_MS` | 默认 120_000 |

**自动发现路径（provider 按顺序搜索 `src/gateway/server.ts`）：**
1. 插件目录内 `~/.hermes/plugins/tdai-memory-openclaw-plugin/`（已安装）
2. `~/.memory-tencentdb/tdai-memory-openclaw-plugin/`
3. `~/.hermes/plugins/tdai-memory-openclaw-plugin/`

## 6.2 安装验证

```bash
# 检查是否安装
ls ~/.hermes/plugins/memory_tencentdb/__init__.py
ls ~/.hermes/plugins/tdai-memory-openclaw-plugin/node_modules/.package-lock.json  # node_modules

# 配置
grep 'memory.provider' ~/.hermes/config.yaml  # 应为 memory_tencentdb
```

## 6.3 启动与验证

Gateway 由提供者的 `GatewaySupervisor` 自动发现并启动，**不需要手动启动**。

```bash
# 检查 Gateway 进程
pgrep -f "memory-tencentdb.*server.ts" && echo "✅ 运行中" || echo "❌ 未运行"

# 健康检查
curl -s http://127.0.0.1:8420/health | python3 -m json.tool
# 期望: {"status":"ok","version":"0.1.0",...}

# L1 记忆搜索（注入的 LLM 工具）
memory_tencentdb_memory_search(query="查询内容")

# 对话搜索
memory_tencentdb_conversation_search(query="查询内容")
```

**数据目录：** `~/.memory-tencentdb/memory-tdai/`

| 路径 | 层级 | 说明 |
|------|------|------|
| `conversations/YYYY-MM-DD.jsonl` | L0 | 原始对话（JSONL，每轮自动记录） |
| `records/YYYY-MM-DD.jsonl` | L1 | 结构化记忆（异步提取） |
| `scene_blocks/*.md` | L2 | 场景块（Markdown，含用户画像） |
| `vectors.db` | — | sqlite-vec 向量库 |

## 6.4 管线触发

L1~L3 提取是异步的。触发条件：

- **L1 提取**：`everyNConversations=5` 次对话，或 `l1IdleTimeout=600s`（10分钟空闲）
- **L2 场景**：L1 完成后等 `l2DelayAfterL1=10s`，`l2MinInterval=900s`
- **L3 人格**：召回时动态合成（`POST /recall`）

**手动触发完整管线：**

```bash
# 获取 session key（从 L0 JSONL）
SESSION_KEY=$(python3 -c "import json; l=open('$HOME/.memory-tencentdb/memory-tdai/conversations/2026-06-06.jsonl').read().strip().split('\n')[-1]; print(json.loads(l)['sessionKey'])")

# 触发 session end → 管线 flush
curl -s -X POST http://127.0.0.1:8420/session/end \
  -H "Content-Type: application/json" \
  -d "{\"session_key\": \"$SESSION_KEY\"}"
# 返回: {"flushed":true}
```

## 6.5 验证端到端（是否需要重启）

```bash
# 1. 喂几条测试对话（跳过原 session 的步骤）
for i in 1 2 3 4 5; do
  curl -s -X POST http://127.0.0.1:8420/capture \
    -H "Content-Type: application/json" \
    -d "{\"session_key\": \"test_$i\", \"user_content\": \"测试: 我叫小王，喜欢跑步\", \"assistant_content\": \"收到\"}"
done

# 2. 结束所有测试 session
for i in 1 2 3 4 5; do
  curl -s -X POST http://127.0.0.1:8420/session/end \
    -H "Content-Type: application/json" \
    -d "{\"session_key\": \"test_$i\"}"
done

# 3. 等 15s 让异步管线完成
sleep 15

# 4. 检查 L1 记录
cat ~/.memory-tencentdb/memory-tdai/records/*.jsonl 2>/dev/null  # 应有记录

# 5. 检查 L2 场景
ls ~/.memory-tencentdb/memory-tdai/scene_blocks/    # 应有 .md 文件
```

## 6.6 常见故障

| 症状 | 根因 | 解决 |
|------|------|------|
| `LLM extraction failed: You didn't provide an API key` | Gateway 没读到 LLM 凭证 | 写 `tdai-gateway.yaml` 或设 `TDAI_LLM_API_KEY` env var（不是 MEMORY_TENCENTDB_LLM_*） |
| `EADDRINUSE port 8420` | 多 Gateway 进程抢端口 | 杀掉所有 `pkill -9 -f "memory-tencentdb"`，让 supervisor 自动重启 |
| `embeddingService: false` | sqlite-vec 嵌入器初始化但无数据 | 正常——写入了向量数据后变 true |
| records/ 或 scene_blocks/ 为空 | 管线已触发但不够 5 次对话 | 喂满 5 次对话后等 15s |
| L1~L3 一直为空 | LLM 凭证不对（走 OpenAI 默认，key 为空） | 检查 `TDAI_LLM_BASE_URL` 和 `TDAI_LLM_API_KEY` 是否正确传递 |

## 6.7 持久化

**配置文件（推荐——不受 shell 环境切换影响）：**
```bash
# ~/.memory-tencentdb/memory-tdai/tdai-gateway.yaml
# 包含 server / llm / data 三部分
```

**环境变量（备用——需在 bashrc 或 supervisor 中设置）：**
```bash
# ~/.bashrc
export TDAI_LLM_API_KEY="$MEMORY_TENCENTDB_LLM_API_KEY"
export TDAI_LLM_BASE_URL="${MEMORY_TENCENTDB_LLM_BASE_URL:-https://api.deepseek.com}"
export TDAI_LLM_MODEL="${MEMORY_TENCENTDB_LLM_MODEL:-deepseek-v4-flash}"
```
