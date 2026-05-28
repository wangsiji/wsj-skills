# Hermes Dashboard nginx 配置模板

## HTTPS 版（certbot 自动生成的完整版）

```nginx
# HTTP → HTTPS 跳转
server {
    if ($host = dashboard.example.com) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name dashboard.example.com;
    return 404;
}

# HTTPS 服务
server {
    server_name dashboard.example.com;

    # HTTP Basic Auth
    auth_basic "Hermes Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:9119;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host "127.0.0.1:9119";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location ~ /\.env|\.git|node_modules {
        deny all;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/dashboard.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
```

## 纯 HTTP 版（测试用）

```nginx
server {
    listen 80;
    server_name dashboard.example.com;

    auth_basic "Hermes Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:9119;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host "127.0.0.1:9119";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```
