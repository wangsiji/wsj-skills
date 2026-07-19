# nginx 静态文件服务配置

## 知识卡片对外访问

在 `wangsiji.site` 上通过 `/cards/` 路径公开访问知识卡片 HTML：

```nginx
location /cards/ {
    auth_basic off;
    alias /var/www/knowledge-cards/;
}
```

文件部署路径：`/var/www/knowledge-cards/{文件名}.html`
对外链接：`https://wangsiji.site/cards/{文件名}.html`

⚠️ `/var/www/knowledge-cards/` 属 root 所有，写入需 `sudo cp`。

## 常见坑

### sites-enabled 不是 symlink

本机 `/etc/nginx/sites-enabled/hermes-dashboard` 是**独立文件**（非软链），
编辑 `sites-available/` 后必须 `cp` 到 `sites-enabled/` 才能生效。

```bash
sudo cp /etc/nginx/sites-available/hermes-dashboard /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```
