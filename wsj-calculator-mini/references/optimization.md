---
name: wsj-miniprogram-optimization
description: 富足人生小程序开发优化——诊断排查/精简策略/页面结构规范/常见Bug模式/设计规范。
---

## 三、开发优化（Optimization）

### 开发原则

**先独立交付，再迭代**：开发第一版时不提问自己做决定，完成后用户 review 再迭代。不要一直问用户确认每个细节。

### 诊断优先

用户说"小程序有问题"时，按以下顺序系统排查：

```bash

### 设计规范

#### 导航栏统一规范

```css
.nav-bar { height: 44px; display: flex; align-items: center; padding: 0 20px; border-bottom: 1px solid #161618; }
.back-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: #141416; border: 1px solid #1e1e22;
  border-radius: 8px; font-size: 20px; color: #fafafa;
}
.nav-title { font-size: 16px; font-weight: 700; color: #fafafa; margin-left: 8px; }
```

#### 全局样式

```css
page {
  background-color: #0a0a0f;
  color: #e4e4e7;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}
button::after { border: none; }
::-webkit-scrollbar { display: none; }
```

#### 计算器类 UI 通用模式

**空状态引导**：首次打开时不要显示空白表单，加引导提示。

**Input/Result 分离**：计算结果不要写回输入框。结果只存入 `resultSummary`，输入框不受影响。当求解目标本身就是输入字段时，**隐藏整个输入段**而非只禁用字段。

**solvedValue**：`ResultSummary` 新增 `solvedValue` 字段，按模式展示正确答案（终值/本金/月投入/收益率%/年限年）。

**totalContrib 公式**：`totalContrib = PMT * years * periodsPerYear`。

**localStorage 持久化**：表单数据自动保存，退出再进不丢失。

**重置功能**：一键恢复默认值，挂页脚文字防误触。

### 上线前检查清单

#### 基础检查
- [ ] Build 无报错
- [ ] dist/ 构建产物已提交
- [ ] pages.json 配置正确（无 `lazyCodeLoading`）
- [ ] 无 template 拼写错误
- [ ] 无重复 `<script>` 块
- [ ] 导航栏样式统一

#### 工程与性能检查
- [ ] **死代码**：App.vue 启动屏是否 `onLaunch` 秒关 → 删除
- [ ] **console.log**：生产中无调试输出
- [ ] **包体积**：单页 app 应 < 300KB
- [ ] **大数据上限**：genSchedule 类函数有 maxCount 参数
- [ ] **动态 label 正确性**：所有文案随频率/模式联动
- [ ] **基准验证**：对比 calculator.net 验证 5 种模式 ✅
- [ ] **构建验证**：`git status dist/` 无残留

