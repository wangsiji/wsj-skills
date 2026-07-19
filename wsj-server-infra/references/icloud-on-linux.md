# iCloud on Linux — 真相

## 结论：Linux 无法原生访问 iCloud Drive

iCloud Drive 使用 Apple 私有 CloudKit API，**没有** Linux 客户端，也没有公开 WebDAV 接口。

## 常见误区

### ❌ icloud-for-linux (snap)
- 是一个 Qt 图形桌面应用（`snap install icloud-for-linux`）
- 需要 GNOME 图形会话 + X11/Wayland 环境
- **无法在纯命令行 VPS 上运行**（Xvfb 虚拟帧缓冲不够）
- 功能：Calendar、Contacts、Drive、Notes、Photos 等（通过模拟 iCloud 网页版）
- 在有桌面的 Linux 上可能可用，但树莓派级别性能很差

### ❌ iCloud WebDAV（icloud.com/icloud-drive）
- iCloud **不提供**公开 WebDAV 端点
- `icloud.com/icloud-drive` 返回 404
- 任何 davfs2/curl WebDAV 方案均不可行

### ❌ rclone iCloud
- rclone **从未发布** iCloud Drive 后端
- GitHub issues 已关闭，永远不会做

### ❌ pyiCloud / icloudfs
- 只能同步**照片**（CloudKit Photos API）
- **无法访问** iCloud Drive 文件（Notes、Documents 等）

## 正确的同步架构

对于 Obsidian 笔记库：

```
Mac ↔ iPhone：iCloud 原生同步（Obsidian iOS app + Mac app）
    ↓（Mac 本地文件夹）
Mac → VPS：Syncthing（点对点增量同步）
```

Mac 上 Obsidian 的库文件在本地，通过 Syncthing 同步到 VPS，不需要 Linux 访问 iCloud。

## 唯一的 Linux iCloud 照片方案

```bash
# 使用 pyicloud Fotos API（仅照片）
pip install pyicloud
python3 -c "
from pyicloud import PyiCloudService
api = PyiCloudService('email', 'password')
api.photos.download_photos('.', album='All Photos')
"
```

这需要 Apple 双重认证，不适合自动化场景。
