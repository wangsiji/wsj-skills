---
name: screenshot-parsing
description: COROS截图解析：类型A乳酸阈/类型B周计划OCR坐标规则 + Obsidian Tasks写入格式
---

## COROS 截图解析

COROS 截图分两种类型，处理方式不同：

### 类型A：乳酸阈心率/配速区间截图

用 `scripts/coros_zone_reader.py` 读取，或直接用 `vision_analyze` 描述即可。提取 LTHR、Max HR、Resting HR 后更新当前分区表。

```bash
python3 /home/wangsiji/.hermes/skills/custom/running-coach/scripts/coros_zone_reader.py /path/to/screenshot.jpg
```

1. 用 Vision 读取 6 个区间的心率/配速数值
2. 提取 LTHR、Max HR、Resting HR
3. 更新当前心率分区表（会话内有效）
4. 后续训练建议直接使用截图数值

**LTHR 优先级：** COROS 截图数据 > 本技能硬编码值。每次截图更新后，下次训练反馈使用新数据。

### 类型B：训练计划日历截图（周视图）

当用户发来 COROS App 的周训练计划截图（显示未来一周每天的跑量/力量安排）：

**首选（vision_analyze 可用时）：** 直接描述截图内容，提取每日训练类型、用时、距离、TL。

**兜底（vision_analyze 不可用 / 无 vision provider）：** 

**首选：** 用 rapidocr-onnxruntime（已预装）进行 OCR 提取：

```python
from rapidocr_onnxruntime import RapidOCR
engine = RapidOCR()
result, elapse = engine('/path/to/screenshot.jpg')
```

**备选（rapidocr 效果不佳时）：** 用 pytesseract + 图片放大增强：

```bash
# 一次性安装
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
```

```python
from PIL import Image, ImageEnhance
import pytesseract

img = Image.open('/path/to/screenshot.jpg')
w, h = img.size
img = img.resize((w*3, h*3), Image.LANCZOS)          # 3x放大
img = ImageEnhance.Contrast(img).enhance(1.8)         # 增强对比度
img = img.convert('L')                                 # 转灰度
text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 6')
```

**pytesseract 加速技巧：** 把输出重定向到文件再 cat，避免终端超时：
```bash
python3 << 'PYEOF' > /tmp/ocr_output.txt 2>&1
...pytesseract code...
PYEOF
cat /tmp/ocr_output.txt
```

**OCR 后解析逻辑：** 详见 `references/tooling-details.md#ocr-坐标解析`（y 分层、x 坐标映射、力量合并规则、输出结构示例）。

### 普通图片/App截图（无 COROS 特征）

当 vision_analyze 不可用时，同类型B的 rapidocr-onnxruntime 流程：
```bash
python3 -c "
from rapidocr_onnxruntime import RapidOCR
import json
engine = RapidOCR()
result, elapse = engine('/path/to/screenshot.jpg')
for item in result:
    print(item[1])
"
```

### 训练计划 → Obsidian Tasks 记录

解析出训练计划后，记录到 `~/projects/wsj-second-brain/01-Projects/Routine/马拉松比赛.md`。

**COROS 阶段名对照：**

COROS 训练计划截图顶部有阶段名（如"第零阶段"、"第一阶段"），需要识别后转为清晰的中文阶段名写入：

| COROS 阶段 | 写入阶段 |
|-----------|---------|
| 第零阶段 | 第零阶段，COROS 基础期 |
| 第一阶段 | 第一阶段，COROS 基础期 |
| 第二阶段 | 第二阶段，COROS 爬坡期 |
| 第三阶段 | 第三阶段，COROS 巩固期 |
| 第四阶段 | 第四阶段，COROS 赛前期 |
| 最后一周（半马测试周） | 第四阶段，COROS 决赛周 |

**格式（Obsidian Tasks 标准格式，用户校正后确认）：**

```
##### 第XX周（对应阶段名）

- [ ] 训练内容 📅 YYYY-MM-DD
- [ ] 训练内容 📅 YYYY-MM-DD
...
```

**COROS 周布局规则（⚠️ 最重要）：** 截图上显示的训练分布在特定日期列中，COROS 默认周视图是 **周一休息、周日长距离**：
- **周一** = 休息日（最多安排力量训练，不安排跑步）
- **周日** = 长距离跑日
- **周三/周四** = 质量课（间歇/速度/混氧）
- 如果截图显示 6 个训练条目分布在 7 个日期标签上 → 第一条对应周二，最后一条对应周日，周一被跳过

**规则：**
- 每条任务是独立的一行 `- [ ] 训练内容 📅 YYYY-MM-DD`，不要用 `• 任务:` 格式（2026-06-09 用户纠正）
- 同一天有跑步+力量训练，**拆成两条独立任务**（不要合并到同一行）：
  ```
  - [ ] 12k轻松跑 📅 2026-06-15
  - [ ] 上肢力量（38组）📅 2026-06-15
  ```
- 休息日写 `- [ ] 休息 📅 YYYY-MM-DD`
- 星期**不需要**单独写一行 — 日期在 Obsidian Tasks 的 `📅` 字段中体现
- 每周末的休息日单独写 `- [ ] 休息 📅 YYYY-MM-DD`
- 使用 Obsidian Tasks 格式 `📅 YYYY-MM-DD`（非 Dataview `due::`）
- 先读现有文件，追加到目标马拉松的 `### 训练记录` → `#### 第二阶段：YYYYMMDD-YYYYMMDD` 下
- 同时更新 frontmatter 的 `modified` 字段
- 如有多周截图，**全部 OCR 解析后一次写入**，不要一周一周分开

**⚠️ 禁止用 read_file() 读取后写回**: read_file 在每行前加 `N|` 行号前缀（如 `1|---`），直接写回会污染 YAML frontmatter 和 markdown 格式。  
- 正确：`with open(path) as f: lines = f.readlines()`  
- 错误：`content = read_file(path)["content"]` — 含有行号前缀  
- **已污染修复**：`sed -i 's/^[0-9]*|//' 马拉松比赛.md`  
- **最佳实践**：用 `terminal` 直接运行 Python，用 `cat` 确认内容，用 `open()` + `writelines()` 写入

**文件索引漂移陷阱（重要）：** 当 马拉松比赛.md 经历过多次修改（sed 修复前缀 + Python 写入 + 追加），行号索引会与最初计算的偏移量不一致。不要在脚本中硬编码行号（如 `lines[376:713]`），而是动态查找关键锚点：  
```python
for i, line in enumerate(lines):
    if "## 2025三亚" in line:
        sanya_start = i
    if "## 2026 下半年训练计划" in line:
        old_section_start = i
```
每次构造文件前重新读取，不要依赖之前会话中计算好的行号。

**文件构造后验证清单（必做）：**
```bash
grep -n "^## " 马拉松比赛.md    # 确认所有马拉松标题
grep -c "2025三亚\|2025南通\|2023荣成\|2026云南" 马拉松比赛.md  # 应为 4
```
确认每场比赛的 `### 照片&成绩证书` 和 `### 总结` 子节没有被截断。

**多周批量写入策略：**

当用户一次性发来多周截图（如 12 周完整计划）：  
1. 全部 OCR 后再开始写文件  
2. 按 COROS 阶段分组（第零~第四阶段）  
3. 一次性写入，覆盖该训练周期下的所有周  
4. 删除旧的 bullet-list 格式计划（如果有），只保留 Obsidian Tasks 格式

**文件损坏恢复：** 如果不慎用 read_file 的行号前缀污染了文件，或写入了错误的结构：  
1. 优先从备份恢复（`马拉松比赛.md.bak`、`.bak2`、`.bak3`）  
2. 如果没有可用备份，请用户提供需要恢复的章节原文（截图/复制）。用户直接发来的 markdown 是最可靠的恢复源  
3. 用 ```` 围住的块直接写入文件，不要二次解析

**配速3区快速参考（LTHR 4'25"/km）：**

| 区 | 配速 |
|----|------|
| E 轻松跑 | 5'11"–6'13" |
| T 阈值 | 4'20"–4'45" |
| I 间歇 | < 4'20" |

---

