# Vision 配置

> Hermes `browser_vision` / `vision_analyze` 的辅助视觉模型配置。主文件见 `SKILL.md` 任务路由。

- Provider: openrouter
- Model: openai/gpt-4o
- API key: 在 `~/.hermes/.env`（`OPENROUTER_API_KEY`），base64 写入绕过脱敏
- 读取方式：config.yaml 的 `auxiliary.vision.api_key`
- ⚠️ `browser_vision` / `vision_analyze` 报错 `No LLM provider configured` → 见 [references/vision-troubleshoot.md](vision-troubleshoot.md)
