# FreshRSS Google Reader API 调试笔记（2026-05-12）

## 背景
FreshRSS 已部署在 `http://192.3.16.123:8386`，API 已开启。调试过程发现大量坑。

---

## 认证流程（关键发现）

### 步骤1: 获取 Auth Token
```bash
# POST 到 /accounts/ClientLogin（注意不是 /api/greader.php/accounts/ClientLogin）
# 参数是 Email= 和 Passwd=（注意是 Passwd 不是 Pass）
curl -s -X POST "http://192.3.16.123:8386/api/greader.php/accounts/ClientLogin" \
  -d "Email=wangsiji@buaa.edu.cn&Passwd=1993wang123704"

# 返回格式：
# SID=wangsiji@buaa.edu.cn/<sha1_token>
# Auth=wangsiji@buaa.edu.cn/<sha1_token>
```

### 步骤2: 使用 Token 调用 API
```bash
# Authorization 头的格式：GoogleLogin_auth=<email>/<sha1_token>
curl -s -H "Authorization: GoogleLogin_auth=wangsiji@buaa.edu.cn/<sha1_token>" \
  "http://192.3.16.123:8386/api/greader.php/reader/api/0/subscription/list?output=json"
```

---

## URL 格式（最容易搞错）

### 正确格式
```
/api/greader.php/reader/api/0/subscription/list
/api/greader.php/reader/api/0/stream/contents/feed/2
/api/greader.php/accounts/ClientLogin
```

### 错误格式（我踩过的）
```
❌ /api/greader.php/api/0/...          ← 多了 /api
❌ /api/greader.php/0/...              ← 少了 /reader/api/
❌ Authorization: Basic ...            ← 不是 Basic Auth，是 GoogleLogin_auth
```

---

## PHP 手动计算 Token（用于调试）
```php
<?php
// 在容器内计算 token
$salt = '343bf58639a98578c35b7273ddf938787912dcb98032ef8258723efe8173b19e';
$user = 'wangsiji@buaa.edu.cn';
$hash = '$2y$09$du5Vhoqew9mLchYUeU/BMeE7yyw4JV7QE94blFUVIWGma/w0JRvYO';
$token = sha1($salt . $user . $hash);
// 返回: 71802a02a7907a198b256b4e7da9e16c4153b3cc
```

---

## 添加订阅的正确方式

### 方式1: quickadd（最简单）
```bash
curl -s -X POST "http://192.3.16.123:8386/api/greader.php/reader/api/0/subscription/quickadd" \
  -H "Authorization: GoogleLogin_auth=<token>" \
  -d "quickadd=http://example.com/feed.xml"
# 返回: {"numResults":1,"streamId":"feed/3","streamName":"Feed Name"}
```

### 方式2: subscription/edit
```bash
curl -s -X POST "http://192.3.16.123:8386/api/greader.php/reader/api/0/subscription/edit" \
  -H "Authorization: GoogleLogin_auth=<token>" \
  -d "s=feed/http://example.com/feed.xml&t=Feed Name&ac=subscribe"
```

---

## Fever API（备用）
- URL: `http://192.3.16.123:8386/api/fever.php`
- 认证：`auth` 始终返回 0（未连通）
- Fever Key 在用户配置里：`fc2dbb0cd1ce4934ef5ad74ff31db89f`
- Fever API 调试价值不大，专注 Google Reader API 即可

---

## Docker 环境信息

```
容器名: freshrss
镜像: freshrss/freshrss
端口: 8386
数据卷: /home/wangsiji/freshrss/data → /data (容器内)
用户配置: /var/www/FreshRSS/data/users/wangsiji@buaa.edu.cn/config.php
API Hash: $2y$09$du5Vhoqew9mLchYUeU/BMeE7yyw4JV7QE94blFUVIWGma/w0JRvYO
Salt: 343bf58639a98578c35b7273ddf938787912dcb98032ef8258723efe8173b19e
```

---

## 快速测试命令
```bash
# 1. 获取 token
TOKEN=$(curl -s -X POST "http://192.3.16.123:8386/api/greader.php/accounts/ClientLogin" \
  -d "Email=wangsiji@buaa.edu.cn&Passwd=1993wang123704" | grep "^Auth=" | cut -d= -f2)
echo "Token: $TOKEN"

# 2. 列出订阅
curl -s -H "Authorization: GoogleLogin_auth=$TOKEN" \
  "http://192.3.16.123:8386/api/greader.php/reader/api/0/subscription/list?output=json"

# 3. 获取某个 feed 的内容
curl -s -H "Authorization: GoogleLogin_auth=$TOKEN" \
  "http://192.3.16.123:8386/api/greader.php/reader/api/0/stream/contents/feed/2?output=json&n=5"
```

---

## RSSHub Docker（与 FreshRSS 配合）

```bash
# 启动 RSSHub
sudo docker run -d --name rsshub \
  -p 8280:3000 \
  -e PORT=3000 \
  -e NODE_ENV=production \
  diygod/rsshub:latest

# 可用 route（实测）
# ✅ 小宇宙播客: /xiaoyuzhou/podcast/<pid>
# ❌ B站视频: /bilibili/user/video/<mid> — 需要 Playwright（浏览器），默认镜像没有
# ❌ 微信公众号: /wechat/mp/<biz> — 服务不稳定

# B站需要 Playwright（未成功安装）
# 容器内执行: npm install playwright && npx playwright install chromium
# 失败原因: npm 依赖冲突（eslint-nibble peer dependency issue）
```

---

## 已知问题

1. **B站 RSS**: RSSHub 默认镜像不包含 Playwright，无法抓取 B站（需要浏览器渲染）
2. **微信公众号**: RSSHub 的 wechat route 不稳定
3. **Playwright 安装**: RSSHub Docker 内 npm 依赖冲突，无法直接安装 Playwright
4. **Fever API**: 返回 `auth:0`，认证不通，专注 Google Reader API 即可
