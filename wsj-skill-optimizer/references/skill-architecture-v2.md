# Skill 架构重构框架（v2 模式）

> 当某 skill 膨胀到 1000+ 行、规则分散多处、模型"读懂了但执行变慢抓不住重点"时，按此框架工程化重构。来源：用户 2026-07-19 对 qiuqiu-content 的诊断 + 落地 v2（128 行主文件 + 11 references）。

## 核心判断

优化方向不是"继续加规则"，而是：

> 把"1000 行经验"压缩成"200 行执行规则 + references 知识库"。

评估维度（满分 100）：人设还原 / 经验沉淀 / 可执行性 / Agent 调用效率 / 长期维护性。当"调用效率"和"维护性"明显偏低时，需要 v2 重构。

## 十点重构法

1. **拆层（路由 + 知识库）**：主文件只做"触发 → 读哪些 reference → 执行什么流程"，不承担知识库。细节全下沉 `references/`。主文件目标 ≤200 行。
2. **优先级系统（Rule Priority）**：冲突时听谁。P0 人设真实性（禁编造）> P1 已发布规律 > P2 目标（读者价值>表达欲）> P3 技巧 > P4 格式。
3. **Task Router**：触发后先分类再执行。C（修改）检测已有文章→跳过重选题/搜素材/人设校准。
4. **踩坑→可执行规则**：故事性踩坑转 `RULE-01~N`（禁止/必须+原因），不读故事。
5. **Pre/Post Check**：检查表提前到生成前，生成后复查。
6. **删过细规则到 references**：具体编辑修改归档 `editorial-history.md`，不占主文件。
7. **输入输出协议**：输入 `task/topic/audience/goal/source_material/tone`；输出固定结构（标题×5→角度→正文→配图→检查）。
8. **Never Do 集中**：所有禁止行为集中一处。
9. **动态记忆接口（可选）**：轻量 `references/<name>-profile.md` 摘要；勿建独立 yaml（vault 已有则复用，不双源）。
10. **黄金 N 条置顶**：模型执行时的短版最高优先级规则，放主文件顶部。

## 重构步骤

```
1. 备份：cp SKILL.md SKILL.md.bak.$(date +%Y%m%d)v2
2. 验证真实重复点（grep 关键标题次数，别凭印象）
3. 重写主文件为路由版（≤200行）
4. 从旧文提取细节建 references（mindset/writing-rules/article-patterns/mistakes/editorial-history/image-rules…）
5. 主文件导航表逐行指向 references
6. 断链校验 + frontmatter 校验
```

## 真实重复信号（该下沉/合并）

- 同一标题出现 ≥2 次 → 只留黄金N条+Never Do 各提一次
- 踩坑按日期重复记两遍 → 合并去重进 RULE 集
- 禁止/不要类分散 40+ 处 → 集中 Never Do + RULE 集
- 7 节结构定义两遍（格式+指南）→ 合并下沉

## 边界（不删什么）

- 踩坑/RULE 是经验资产，转格式不删内容
- 配图流程/坑记录（如 merge-clip.py 已知坑）是防回归资产，保留
- vault 类"数据完整>美化"仍适用（不删任务/日志）

## 落地样本

- `qiuqiu-content`：1085 行单文件 → 128 行主文件 + 11 references（v2）。黄金10条+Rule Priority+Router A-G+协议+Never Do+Pre/Post Check 全落地。
- `running-coach`：626→409 行，references 12 个。
- `self-hosted-infra`：823→358 行，references 15 个。
- `knowledge-card`：573→462 行，写作指南下沉。
