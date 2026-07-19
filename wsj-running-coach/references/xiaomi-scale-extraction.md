---
name: xiaomi-scale-extraction
description: 小米体脂秤SmartScaleConnect提取全流程（2026-06探测，结论：全部路径不可用）
---

# SmartScaleConnect — 小米体脂秤数据提取

## 概述

[SmartScaleConnect](https://github.com/AlexxIT/SmartScaleConnect) 是一套 Go 写的体重数据同步工具，支持从小米/米家生态（体脂秤、身体成分秤）拉取数据，导出到 CSV/JSON 或同步到 Garmin/Home Assistant。

本参考文档记录了 小米体脂秤S400 国行版 + 米家App 的数据提取过程。

## 工具安装

| 下载 | 命令 |
|------|------|
| 二进制 | `curl -sL https://github.com/AlexxIT/SmartScaleConnect/releases/download/v0.4.1/scaleconnect_linux_amd64 -o scaleconnect && chmod +x scaleconnect && sudo mv scaleconnect /usr/local/bin/` |
| 源码编译（无预编译二进制时） | 下载 Go 1.24+ → `git clone repo && cd repo && go build -o scaleconnect .` |
| 验证 | `scaleconnect -h` |

v0.4.2 仅有源码，需 Go 1.24+ 编译。安装路径：`~/go/bin/SmartScaleConnect`。

## 支持的 App/秤对应关系

| 秤型号 | App | 配置格式 |
|--------|-----|---------|
| 小米体脂秤S400 国行 (MJTZC01YM, yunmai.scales.ms103) | 米家 / Mi Fitness | `xiaomihome 邮箱 密码 cn yunmai.scales.ms103` |
| 小米体脂秤S400 欧版 (MJTZC01YM, yunmai.scales.ms104) | 米家 | `xiaomihome 邮箱 密码 eu yunmai.scales.ms104` |
| 小米体脂秤2 (XMTZC05HM) | Zepp Life | `zepp/xiaomi 邮箱 密码` |
| 小米8电极体脂秤 (XMTZC01YM, yunmai.scales.ms3001) | Mi Fitness | `mifitness 邮箱 密码 yunmai.scales.ms3001` |

## 小米登录 API 变更（2026-06 探测结果）

2026年6月探测发现 Xiaomi 登录流程已变更：

### 旧 API 失效

| 旧端点 | 状态 |
|--------|------|
| `account.xiaomi.com/pass/serviceLogin?_json=true&sid={sid}` | ✅ 仍可用，但返回 code=70016 + 重定向到新登录页 |
| `account.xiaomi.com/pass/serviceLoginAuth2` | ❌ 返回 10025「系统错误」(实际是设备验证) |
| `account.xiaomi.com/pass/sendPhoneTicket` | ⚠️ 未知，需配合新流程 |

### 新登录页

- **URL**: `https://account.xiaomi.com/fe/service/login/?sid={sid}&_json=true`
- **React SPA**，需要 JavaScript 渲染
- 登录后状态：`/fe/service/login/password?sid={sid}&_json=true`
- 需要处理：复选框「已阅读并同意...」、弹窗「同意并继续」

### 错误码 10025（设备验证）

密码登录失败返回 error 10025「系统错误，请稍候再试」。实际含义：

- 小米要求**已登录过的可信设备**授权
- 常见于新 IP、新设备、长时间未登录的账号
- 绕过方式：
  - **方法A**：短信验证码（触发 SMS → 用户输入码 → 完成登录）
  - **方法B**：用米家 App 扫码（需中国区服务器二维码）
  - **方法C**：使用已缓存的 token（`scaleconnect.json` 中的 serviceToken）

### Playwright 自动化登录流程

适用于 Python 环境，完整流程：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    page = p.chromium.launch(headless=True).new_page()
    page.set_viewport_size({"width": 1280, "height": 900})
    
    # 1. 打开新登录页
    page.goto(f"https://account.xiaomi.com/fe/service/login/?sid={sid}&_json=true")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    
    # 2. 填写凭证
    page.fill('input[name="account"]', phone)
    page.fill('input[name="password"]', password)
    
    # 3. 勾选协议复选框
    cb = page.locator('input[type="checkbox"]').first
    if cb.count() > 0 and not cb.is_checked():
        cb.click()
    
    # 4. 点击登录
    page.click('button:has-text("登录")')
    page.wait_for_timeout(3000)
    
    # 5. 处理协议弹窗
    agree = page.locator('button:has-text("同意并继续")')
    if agree.count() > 0 and agree.is_visible():
        agree.click()
        page.wait_for_timeout(5000)
    
    # 6. 检查结果
    # 成功：URL 离开 login 页面
    # 失败：仍显示密码登录页，且有 error 10025 文字
```

### SMS 验证码流程

Playwright 可自动化触发发送短信，然后人工输入验证码：

```python
other = page.locator('button:has-text("其他方式登录")')
other.first.click()
sms_btn = page.locator('button:has-text("短信"), span:has-text("短信")')
sms_btn.first.click()
page.fill('input[name="account"]', phone)
send_btn = page.locator('button:has-text("发送"), button:has-text("获取")')
send_btn.first.click()

code = input("请输入短信验证码: ")
code_input = page.locator('input[type="text"], input[type="tel"]').first
code_input.fill(code)
page.locator('button:has-text("验证"), button:has-text("登录")').first.click()
page.wait_for_timeout(5000)
```

## token 复用

SmartScaleConnect 首次成功登录后会在 `scaleconnect.json` 中缓存 token。后续执行相同配置时自动使用缓存 token，无需重复登录。

```yaml
sync_xiaomi_s400:
  from: xiaomihome username password cn yunmai.scales.ms103
  to: csv /tmp/xiaomi_scale_data.csv
```

## 已知问题

| 问题 | 说明 |
|------|------|
| `Get \"\": unsupported protocol scheme \"\"` | Xiaomi 登录返回空 location（需设备验证），非工具 bug |
| 小米API变更风险 | 工具最后更新于 2025-08，Xiaomi 于 2026年变更了登录流程（SPA新登录页） |
| 密码登录后 location 为空 | securityStatus!=0 表示需要额外验证 |
| **错误 10025** | 「系统错误，请稍候再试」= **设备验证**，非 bug。需短信验证码或可信设备授权 |
| **扫码显示「地区不支持」** | 工具生成二维码指向国际版米家。中国区账号不走扫码，走短信验证或缓存 token |
| **S400 数据模型** | `yunmai.scales.ms103` 是云麦方案。米家 App 内绑定并正常使用后，云端才有历史数据。新买的秤需先通过米家 App 绑定并测量一次 |

## 小米 API 真实状态（2026-06）

经过完整探测，当前 Xiaomi API 对非可信设备的访问几乎完全封锁：

### 密码直连（完全不可行）

- 旧 API `account.xiaomi.com/pass/serviceLoginAuth2` → 全部返回 10025
- `python-miio` 库的 `micloud` 模块 → 同样 Access Denied
- 所有 SID 测试（xiaomiio、miothealth、passport）→ 全部 70016 + 新 SPA 跳转

### Playwright 自动化登录（部分可行，卡在设备验证）

- 新 SPA 登录页 (`/fe/service/login/`) 可用 Playwright 自动填写 + 提交
- 但提交后：URL 停留在 `/login/password?sid=xiaomiio` 页面，显示错误 10025
- **中国区账号在新登录页看不到短信验证码选项**——「其他方式登录」仅显示 Facebook/Google 等国际社交登录，没有手机验证码
- 小米新版登录页可能根据 IP/请求特征判定为国际用户，隐藏了短信验证入口

### 短信验证码（理论上可行，但入口不可见）

Playwright 可以：
1. ✅ 打开登录页
2. ✅ 填写手机号+密码
3. ✅ 勾选协议
4. ✅ 点击登录
5. ❌ 收到 10025，但页面上没有 SMS 验证码的跳转入口

**可能原因：** 新 SPA 登录页会根据 `sid` 参数显示不同的验证方式。`sid=xiaomiio` 可能没有短信验证权限。需尝试其他 `sid`（如 `sid=passport` 或 `sid=miothealth`）或使用不同登录入口。

### 最终可行的方案

1. **用米家 App 导出 ServiceToken**（需用户操作）
   - 米家 App → 我的 → 设置 → 账号与安全 → 查看 Token
   - 或通过 App 抓包获取 Authorization header
   - 拿到 token 后可直接调 `api.io.mi.com/app` 的 scale API
2. **从已登录设备反向提取**：如果 SmartScaleConnect 曾在某台已认证设备上成功登录过，`scaleconnect.json` 中缓存的 token 仍然有效
3. **放弃自动化，走用户手动**：最简单可靠

## 2026-06 最终结论：自动化体重数据获取不可行

经过完整探测（SmartScaleConnect、micloud、Playwright、coros-mcp 逆向 API），小米/高驰生态的体重/体脂自动化获取**当前不可行**：

- Xiaomi 登录全面封锁：10025 设备验证，新 SPA 登录页无中国区短信入口
- iOS 米家 App 无法获取 ServiceToken
- COROS API 无体重字段
- 用户已明确放弃此路径（"有点复杂，这个先不搞了"）

**唯一可用方案：**
1. **Apple Health 导出**：iPhone 健康 App → 右上角头像 → 导出所有健康数据 → zip 文件可解析（需用户手动操作）
2. **用户口述**：用户通过 Telegram 告知体重，助手续存