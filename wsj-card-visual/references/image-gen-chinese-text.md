# 中文文字渲染 vs AI 生图模型对比

知识卡片需要大量中文文字时，不同生图方式的效果对比：

| 方式 | 中文渲染 | 排版可控 | 成本 | 适用场景 |
|------|---------|---------|------|---------|
| **HTML/CSS 截屏** | ✅ 精准 | ✅ 完全可控 | 免费 | 文字量大的知识卡片首选 |
| **Lovart GPT Image 2** | ⚠️ 较好（有漂移） | ⚠️ 自动 | Lovart 余额 | 快速出图可接受少量文字漂移 |
| **CloudBase 混元生图** | ❌ 不准 | ❌ 不可控 | 10万张免费 | 配图/封面/装饰图 |
| **OpenRouter GPT-5.4 Image 2** | ✅ 好 | ⚠️ 自动 | $0.000008/token | 需付费，需要 OpenRouter 余额 |
| **FLUX (FAL.ai)** | ❌ 不准 | ❌ 不可控 | 内置工具 | 配图/插画 |

## 决策树

```
用户要知识卡片
├─ 文字量大（≥20字中文）→ HTML/CSS → 截屏
├─ 文字量少 + 要设计感 → Lovart GPT Image 2
├─ 纯配图/封面/插画 → CloudBase 混元 / FLUX
└─ 用户明确要求 AI 生图 → 告知中文局限，推荐 Lovart
```

## Lovart GPT Image 2 调用方式

```bash
# 1. 检查项目状态
export LOVART_ACCESS_KEY=ak_xxx
export LOVART_SECRET_KEY=sk_xxx
python3 ~/.hermes/skills/third-party/lovart-skill/agent_skill.py config --json

# 2. 创建项目（首次）
python3 ~/.hermes/skills/third-party/lovart-skill/agent_skill.py create-project

# 3. 生图（指定 GPT Image 2）
python3 ~/.hermes/skills/third-party/lovart-skill/agent_skill.py chat \
  --prompt "设计一张知识卡片..." \
  --prefer-models '{"IMAGE":["generate_image_gpt_image_2"]}' \
  --json --download
```

可选模型：`generate_image_gpt_image_2_high`（高质量）、`generate_image_midjourney`、`generate_image_nano_banana_pro`

## CloudBase 混元生图注意事项

- **水印问题**：混元生图会在右下角自动加「AI生成」水印
- **尺寸限制**：仅支持 1024×1024（正方形），不支持竖版
- **调用方式**：只能通过云函数（服务端），不支持直接 HTTP API
- **触发词**避开：涉及武器、人体等敏感词会被拒
- **改 prompt 不一定能去掉水印**：prompt 加「不要文字」不一定生效，后处理裁剪更可靠

## 用户配色偏好（Apple 极简白风）

- 外背景: `#f5f5f7`
- 卡片底色: `#ffffff`
- 主色: `#007AFF`（苹果蓝）
- 橙色点缀: `#FF9500`
- 绿色: `#34C759`
- 紫色: `#AF52DE`
- 红色(错误): `#FF3B30`
- 标题色: `#1d1d1f`
- 正文字: `#515154`
- 辅助文字: `#6e6e73`/`#86868b`
- 边框: `#e8e8ed`
- 圆角: 大24-32px / 中12-16px / 小8-10px
