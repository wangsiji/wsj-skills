# Dashboard 子路径部署 + 多服务同域名 — 参考配置

## 实际案例：Dashboard (/hermes/) + 静态站点 (/feed/)

以下配置来自 wangsiji.site 的正式部署：

```nginx
server {
    server_name dashboard.wangsiji.site wangsiji.site;

    # 公开静态站点
    location /feed {
        auth_basic off;
        alias /var/www/info-feed/;
        try_files $uri $uri/ /feed/index.html =404;
    }

    # Dashboard 在子路径
    location /hermes/ {
        auth_basic "Hermes Dashboard";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://127.0.0.1:9119/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host "127.0.0.1:9119";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /hermes;

        proxy_read_timeout 86400;
    }

    # 根路径 → 跳转到公开页面
    location = / {
        auth_basic off;
        return 302 /feed/;
    }

    # 禁止访问敏感路径
    location ~ /\.env|\.git|node_modules {
        deny all;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/wangsiji.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wangsiji.site/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

# HTTP → HTTPS 跳转
server {
    if ($host = wangsiji.site) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name dashboard.wangsiji.site wangsiji.site;
    return 404;
}
```

## 关键点回顾

| 要点 | 说明 |
|------|------|
| `proxy_pass http://127.0.0.1:9119/;` | 末尾带 `/`，剥离 `/hermes/` 前缀 |
| `X-Forwarded-Prefix /hermes` | Dashboard 内部路由需要这个前缀 |
| `auth_basic off` on `/` + `/feed` | server 块级的 auth 不会自动跳过 redirect 或 alias location |
| Dashboard 服务状态 | `sudo systemctl status hermes-dashboard` — 不在运行则 `/hermes/` 返回 401（nginx auth 通过了但后端没响应） |
