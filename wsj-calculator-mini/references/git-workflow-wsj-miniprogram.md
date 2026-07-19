# wsj-miniprogram Git Workflow

## 仓库信息
- 远程仓库：https://github.com/wangsiji/wsj-miniprogram（私人仓库）
- 项目目录：`/home/wangsiji/projects/wsj-miniprogram`
- 默认分支：`main`（注意不是 master）

## 初始化新仓库（已有项目）
```bash
cd /home/wangsiji/projects/wsj-miniprogram
git init
git config user.email "qiubai_happy@163.com"
git config user.name "wang siji"
git add -A
git commit -m "init"
git branch -M main
gh repo create wsj-miniprogram --private   # 如果仓库不存在
git remote add origin https://github.com/wangsiji/wsj-miniprogram.git
git push --set-upstream origin main
```

## push.sh 脚本
位置：`/home/wangsiji/projects/wsj-miniprogram/push.sh`
```bash
#!/bin/bash
set -e
cd /home/wangsiji/projects/wsj-miniprogram
git add -A
read -p "commit 描述: " msg
[ -z "$msg" ] && echo "跳过" && exit 0
git commit -m "$msg"
git push origin main
```

## Git 陷阱
- **分支名**：GitHub 默认是 `main`，不是 `master`。新建仓库后用 `git branch -M main`
- **git init 后的 remote**：如果仓库已存在（gh repo create 报 "Name already exists"），直接 `git remote add origin <url>` 或 `git remote set-url origin <url>`
- **rejected push**：如果远程有 commit（README 等），先 `git pull origin main --allow-unrelated-histories --no-rebase -X theirs` 合并，再用 `git push --force`
- **首次 push 需要 upstream**：`git push --set-upstream origin main`，或设置 `git config --global push.autoSetupRemote true`
