# Vision 故障排查

## 症状

`browser_vision` / `vision_analyze` 报错：
```
No LLM provider configured for task=vision provider=openrouter
```

尽管 `~/.hermes/config.yaml` 中已配置：
```yaml
auxiliary:
  vision:
    provider: openrouter
    model: openai/gpt-4o
    api_key: sk-or-...  # 实际 key
```

## 根因

`auxiliary.vision.api_key` 中的 API key 可能在写入时被截断或覆盖为不完整的值。  
检查方法：`cat ~/.hermes/config.yaml | grep -A6 'vision:'`

若显示 `api_key: sk-or-...ecab` 这类明显截断的 key，说明存储的 key 不完整。

## 修复

1. 从 `.env` 获取完整 key（Hermes 会脱敏显示，用 Python 读取才是原始值）：
   ```bash
   python3 -c "import re; print(re.search(r'OPENROUTER_API_KEY=(.*)', open('/home/wangsiji/.hermes/.env').read()).group(1))"
   ```

2. 将完整 key 写回 config.yaml：
   ```bash
   sed -i "s|api_key:.*|api_key: 完整key|" ~/.hermes/config.yaml
   ```

3. 重启 Hermes 使新配置生效。

## 备用方案

若 key 始终无法通过 config.yaml 读取，可在 Hermes 启动脚本中 export：
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```
然后重启 Hermes 进程。工具会从 os.environ 读取。
