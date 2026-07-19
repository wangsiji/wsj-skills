# wsj-skills

Hermes Agent 自建技能集。

镜像源：`~/.hermes/skills/custom/`

| skill | 功能 |
|-------|------|
| `wsj-clip` | 统一剪藏：网页/公众号/X/B站/播客 → Obsidian |
| `wsj-graphic-thinking` | 结构化解图：Excalidraw 生成 |
| `wsj-knowledge-card` | 常青卡片 7 节蒸馏 |
| `wsj-card-visual` | 图形知识卡片 HTML 生成 |
| `wsj-qiuqiu-content` | 公众号内容创作 |
| `wsj-running-coach` | COROS 跑步教练（破三/减重/肩带） |
| `wsj-server-infra` | 服务器运维 |
| `wsj-calculator-mini` | FIRE 计算器小程序 |
| `wsj-skill-optimizer` | Skill 结构优化器 |

同步方式：

```bash
rsync -av ~/.hermes/skills/custom/ ./ --exclude='*.bak.*'
git add -A && git commit -m "sync" && git push
```
