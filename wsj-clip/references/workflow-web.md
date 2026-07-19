# 网页剪藏详细流程（Method A）

URL 路由 → 并行剪藏原文+AI 总结 → 合并输出到 `00-LLM-WiKi/Raw/`

## URL 路由

| 类型 | 特征 | 方法 |
|------|------|------|
| GitHub | `github.com/<owner>/<repo>` | 抓 raw README（main/master）→ 走 merge-clip.py `github` 类型 |
| 公众号 | `mp.weixin.qq.com` | down.mptext.top API → 降级 curl + 移动端 UA |
| X/Twitter | `x.com/.../status/...` | vnc-clip.py（CDP + 扩展） |
| 其他网页 | 其他 | vnc-clip.py 或 clip.py（备用） |

## 并行执行

剪藏原文和 getnote AI 总结互不依赖，同时启动节省 ~30s。

## 剪藏原文

### 公众号文章

首选 down.mptext.top API，失败降级到 curl + 移动端 UA。详见 `references/down-mptext-api.md`。

**图片文章**（`item_show_type: 8`）：下载图片到 `assets/`，嵌入式 `![page-NN](assets/NN.jpg)`。详见 `references/image-article-handling.md`。

### X/通用网页

```bash
# 主方案（CDP + 扩展）
python3 scripts/vnc-clip.py <URL>

# 备用（headless Chrome --dump-dom）
python3 scripts/clip.py <URL>
```

**执行后**：`find ~/projects/wsj-second-brain -name "*.md" -mmin -3` 定位文件。

### 备用：CDP Direct Extraction

当 Extension SW 不可用时（content script 未注入、扩展配置错误、tab 未找到），vnc-clip.py 自动降级到 CDP 直接 DOM 提取：

| 情况 | 行为 |
|------|------|
| Extension SW 可用 | 正常走 content script → Markdown |
| Extension SW 不可用 | 自动 fallback 到 `Runtime.evaluate` + `document.body.innerText` |
| 两者都失败 | 通知用户 + 建议备用方案 |

CDP 直接提取返回：页面可见文本、标题、URL、innerText（过滤 script/style）。

## AI 总结

详见 `references/getnote-api.md`。

## 合并输出

```bash
python3 scripts/merge-clip.py <type> "<title>" "<author>" "<url>" <body_file> <ai_summary_file>
# type: gzh | x | web | github | bilibili | xiaoyuzhou | douyin
# 参数顺序：body_file 在前，ai_summary_file 在后（与 sys.argv[5]/[6] 一致，勿反）
```

## GitHub 仓库剪藏

README 往往巨大（yt-dlp 179KB 是 manpage），**不要整篇存**，只取价值部分：

```bash
# 1. 分支未知时循环试 main/master，命中非空即停
for b in main master; do
  curl -sL -o /tmp/repo_readme.md -w "HTTP:%{http_code} SIZE:%{size_download} BRANCH:$b" \
    "https://raw.githubusercontent.com/<owner>/<repo>/$b/README.md"
  if [ -s /tmp/repo_readme.md ] && ! head -c 50 /tmp/repo_readme.md | grep -q "404"; then
    echo "FOUND on $b"; break
  fi
done
# 2. 超大文件：用 grep -n "^# " 定位锚点，python 切片取简介+安装+依赖段
# 3. 走 merge-clip.py github 类型 → 输出 Raw/GitHub_<owner>_<repo>.md
```

GitHub 仓库默认无 getnote AI 总结（非文章页），AI 总结由 agent 基于 README 提炼，不调 getnote。
merge-clip.py 参数顺序：**body_file 在前，ai_summary_file 在后**（与 sys.argv[5]/[6] 一致，勿反）。

## 大型 README / manpage 节选技巧

- 用 `grep -n "^# " file.md` 定位章节锚点，用 python 切片 `[start:stop]` 取需要段
- 优先保留：简介、核心特性、安装、用法、架构图；跳过：完整选项参考、依赖清单细节
- 剪藏文件中保留「完整 README」小标题，明确这是节选而非全文

