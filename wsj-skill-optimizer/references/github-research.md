---
name: github-research
description: 本环境无 Firecrawl 额度（web_search/web_extract 不可用）时，用 GitHub API + raw 抓取研究开源 skill 范式的具体命令。
---

# GitHub Research（无 Firecrawl 时）

本环境 `web_search` / `web_extract` 均报 "Web tools are not configured"（无 Firecrawl 额度）。研究开源范式用 GitHub 原生 API + raw 文件，全部走 `curl` / `terminal`。

## 搜仓库（按 star 排序）
```bash
# 关键词搜索
curl -s "https://api.github.com/search/repositories?q=COROS+api&sort=stars&per_page=10" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);[print(f\"  {r['stargazers_count']}★ {r['full_name']} — {r['description'] or ''}\") for r in d.get('items',[])]"

# 组织下搜
curl -s "https://api.github.com/search/repositories?q=org:anthropics+skills&sort=stars&per_page=5"
```

## 读文件（raw.githubusercontent）
```bash
# 官方 skill 样本（看 description 写法 / references 下沉范式）
curl -s "https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/SKILL.md" | head -50

# 列目录树（找 spec / template / 子文件）
curl -s "https://api.github.com/repos/anthropics/skills/contents/spec" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);[print(f['name']) for f in d if isinstance(d,list)]"
```

## 读 README（截断输出，抓 features/tools 段）
```bash
curl -s "https://raw.githubusercontent.com/cygnusb/coros-mcp/main/README.md" | head -80
```

## 实战踩过的坑
- `agentskills.io` 首页是 Next.js 渲染，`curl` 拿不到正文；spec 文档在 `github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md`（但该路径重定向到站点，最终用 `anthropics/skills` repo 的 README + pdf skill 样本反推范式）。
- `api.github.com` 无认证有速率限制（60次/小时），研究够用；批量时加 `sleep` 或错峰。
- 搜索结果 `description` 可能是 None，打印用 `or ''` 防崩溃。
- 不要回退到 `web_search` 重试——本环境稳定不可用，直接走 curl。
