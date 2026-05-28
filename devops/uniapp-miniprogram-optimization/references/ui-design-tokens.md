# 小程序 UI 设计规范（玻璃拟态风格）

## 色彩系统

```css
/* 背景层次 */
--bg-base: #0a0a0f;
--bg-gradient-top: #13131f;  /* 径向渐变顶端 */
--bg-card: rgba(20, 20, 24, 0.8);

/* 边框 */
--border-subtle: rgba(255, 255, 255, 0.04);
--border-card: rgba(255, 255, 255, 0.06);
--border-focus: rgba(99, 102, 241, 0.6);

/* 主色 */
--primary: #6366f1;
--primary-glow: rgba(99, 102, 241, 0.4);
--primary-bg: rgba(99, 102, 241, 0.05);

/* 文字 */
--text-primary: #fafafa;
--text-secondary: #a1a1aa;
--text-muted: #71717a;
--text-dim: #52525b;

/* 图表色 */
--chart-blue: #3b82f6;
--chart-purple: #6366f1;
--chart-green: #22c55e;

/* 圆角 */
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 20px;
--radius-2xl: 24px;
```

## 导航栏

```css
.nav-bar {
  height: 52px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  background: rgba(10, 10, 15, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.back-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  font-size: 22px;
  color: #fafafa;
  transition: background 0.15s;
}
.back-btn:active { background: rgba(255, 255, 255, 0.08); }
```

## 卡片

```css
.card {
  background: rgba(20, 20, 24, 0.8);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
```

## Tab 胶囊

```css
.tab-row {
  display: inline-flex;
  gap: 6px;
  padding: 3px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 14px;
}

.tab-chip {
  padding: 7px 14px;
  border-radius: 11px;
  font-size: 13px;
  font-weight: 600;
  color: #71717a;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.tab-chip.active {
  background: #6366f1;
  color: #fff;
  box-shadow: 0 0 16px rgba(99, 102, 241, 0.4), 0 2px 8px rgba(99, 102, 241, 0.3);
  transform: scale(1.04);
}
```

## 输入框

```css
.form-input {
  width: 120px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #fafafa;
  font-size: 15px;
  text-align: right;
  font-variant-numeric: tabular-nums;
  outline: none;
  padding: 8px 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  border-color: rgba(99, 102, 241, 0.6);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
  background: rgba(99, 102, 241, 0.05);
}
```

## 结果卡片

```css
.result-card {
  background: linear-gradient(145deg, rgba(30, 28, 50, 0.9) 0%, rgba(20, 20, 32, 0.95) 100%);
  border-radius: 24px;
  padding: 28px 20px 24px;
  text-align: center;
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.result-big {
  font-size: 42px;
  font-weight: 900;
  color: #fafafa;
  font-variant-numeric: tabular-nums;
  letter-spacing: -2px;
  line-height: 1;
  text-shadow: 0 2px 12px rgba(99, 102, 241, 0.2);
}

.result-unit {
  font-size: 13px;
  color: #71717a;
  display: block;
  margin-bottom: 20px;
  font-weight: 500;
  letter-spacing: 0.3px;
}
```

## 动画曲线

```css
/* 弹簧动画（Tab、Toggle） */
transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);

/* 进度条过渡 */
transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);

/* Toggle 滑块 */
transition: left 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
```

## 间距规范

```css
/* 页面级 */
.content { padding: 16px 16px 48px; gap: 14px; }

/* 表单项 */
.form-row { padding: 14px 16px; min-height: 52px; }

/* 卡片内 */
.card { padding: 18px 16px; }

/* 标题与内容 */
.card-title { font-size: 14px; font-weight: 700; letter-spacing: -0.2px; }
```

## 字体

```css
font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;
```
