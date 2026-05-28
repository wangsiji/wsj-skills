# Platform RSS Sources — 各平台内容源实测 (2026-05-12 更新)

## Twitter
- **工具**: xreach
- **命令**: `xreach tweets <handle> --count 20 --plain`
- **47个关注账号**: 列表在 `references/twitter-pipeline.md`
- **状态**: ✅ 完全可用，生产环境运行中

## Bilibili
- **UP主RSS**: `https://api.bilibili.com/x/space/wbi/arc/search?mid={MID}&ps=5&order=pubdate&jsonp=jsonp`
- **JSON字段**: `data.list.vlist[].{bvid, title, description, author, aid, created, view, like}`
- **获取MID**: 从 `space.bilibili.com/{MID}` URL 中提取
- **坑（2026-05-12实测修正）**: ⚠️ **不是WBI签名问题**——是B站对海外/数据中心IP的风控限制，RSSHub Playwright能运行但B站直接30秒超时连接拒绝。**IP层面封锁，无法通过RSSHub绕过，需要住宅代理**。
- **状态**: ❌ 海外服务器无法抓取，解法：用户发B站链接给我手动抓
- **已订阅**: mid=14097567（门冬冬，「一人公司」B站账号）

## 小宇宙播客
- **播客页**: `https://www.xiaoyuzhoufm.com/podcast/{PID}`
- **RSS获取**: 从页面 `__NEXT_DATA__` JSON 中提取 episodes（不是标准RSS）
  ```python
  html = curl(url, UA=Mozilla/5.0)
  data = json.loads(re.search(r'<script id="__NEXT_DATA__">(.*?)</script>', html).group(1))
  episodes = data["props"]["pageProps"]["podcast"]["episodes"]
  # 每集: eid, title, description, pubDate, duration, enclosure{url}, playCount
  ```
- **PID来源**: 从播客分享链接提取，如 `xiaoyuzhoufm.com/podcast/6480b91120ec3cbc460382cc`
- **状态**: ✅ 已接入，音频URL可获取
- **已订阅**: PID=6480b91120ec3cbc460382cc（「一人公司」播客）

## 微信公众号
- **RSSHub公共实例**: `https://rsshub.app/wechat/mp/{biz_id}` → ❌ 403 Forbidden
- **自建RSSHub**: Docker镜像 `diygod/rsshub:chromium`（需验证当前可用性）
- **替代方案**: `wechat-article-for-ai` 工具，用户发文章链接 → 逐篇抓取归档
- **biz_id获取**: 从文章链接 `mp.weixin.qq.com/s?__biz={biz}&...` 中提取，base64解码
  ```python
  biz = "Mzg2OTA1OTAxNA=="  # 花叔的biz
  print(base64.b64decode(biz).decode())  # → 3869059014
  ```
- **状态**: ⏳ 待接入，用户提供了花叔biz但还未配置抓取

## FreshRSS (Docker)
- **Docker**: `sudo docker run --name freshrss -p 8386:80 -v /home/wangsiji/freshrss/data:/data` → 已在运行
- **访问**: `http://192.3.16.123:8386`（需初始化向导创建账号）
- **账号**: wangsiji@buaa.edu.cn
- **API端点**: `http://192.3.16.123:8386/api/greader.php`（Google Reader兼容）
- **API认证**: 必须用 ClientLogin → 获取 Auth token → 后续请求用 `Authorization: GoogleLogin_auth=<token>` header
  ```bash
  # Step 1: 获取 Auth Token（POST）⚠️ 参数是 Passwd 不是 Pass
  TOKEN=$(curl -s -X POST "http://192.3.16.123:8386/api/greader.php/accounts/ClientLogin" \
    -d "Email=wangsiji@buaa.edu.cn&Passwd=<API密码>" | grep "^Auth=" | cut -d= -f2)

  # Step 2: 使用 Token
  curl -s -H "Authorization: GoogleLogin_auth=$TOKEN" \
    "http://192.3.16.123:8386/api/greader.php/reader/api/0/subscription/list?output=json"
  ```
- **坑**: URL格式是 `/reader/api/0/...`（不是 `/api/0/...`）；认证token放在header不是URL参数
- **状态**: ✅ 已部署，API已开启，已订阅「一人公司」播客 (feed/2)

## RSSHub (自建 Docker)
- **Docker**: `sudo docker run -d --name rsshub -p 8280:3000 -e PORT=3000 -e NODE_ENV=production diygod/rsshub:latest`
- **宿主机Playwright已挂载**: `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright` + `~/.cache/ms-playwright:/ms-playwright:ro`
- **已安装系统依赖**: libglib2.0-0, libnss3, libatk, libatk-bridge, libcups, libdrm, libxkbcommon, libxcomposite, libxdamage, libxrandr, libgbm, libpango, libcairo, libasound2（20+包）
- **访问**: `http://192.3.16.123:8280`
- **微信公众号路由格式**: `http://192.3.16.123:8280/wechat/mp/{biz_id}`（实测返回 NotFoundError，路由可能需要其他参数）
- **小宇宙播客路由**: `http://192.3.16.123:8280/xiaoyuzhou/podcast/{pid}` ✅ 200 OK
- **Twitter路由**: `http://192.3.16.123:8280/twitter/user/{screen_name}` ❌ 503（需要TWITTER_COOKIES环境变量）
- **B站路由**: ❌ 30秒超时（**VPS IP被B站封禁**，不是Playwright问题，是IP层面封锁）

## 今日已接入的订阅源

| 平台 | 订阅内容 | 采集方式 | 状态 |
|------|---------|---------|------|
| Twitter | 47个关注账号 | xreach CLI + cronjob | ✅ 生产运行中 |
| Bilibili | mid=14097567 门冬冬 | api.bilibili.com | ❌ VPS IP被封 |
| 小宇宙播客 | PID=6480b911 「一人公司」| RSSHub Docker → FreshRSS | ✅ 已订阅 |
| 微信公众号 | 花叔（待接入） | wechat-article-for-ai | ⏳ 待配置 |
| RSS Hub | 自建 Docker | 播客路由可用，其他需配置 | ⏳ |
| FreshRSS | 播客订阅管理 | Docker | ✅ 已部署 |
