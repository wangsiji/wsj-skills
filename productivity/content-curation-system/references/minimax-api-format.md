# MiniMax API — 响应格式与调用坑 (2026-05-12 实测)

## 关键发现

**之前错误**：`data["choices"][0]["message"]["content"]`  
**正确格式**：`data["content"]` 是顶层 list

```python
# 错误 ❌
content = data["choices"][0]["message"]["content"]

# 正确 ✅
for item in data.get("content", []):
    if item.get("type") == "text":
        return item["text"]
```

## 完整调用代码

```python
import urllib.request, json

API_KEY = "sk-cp-pkBPNfAY97fHhEFlnUCCMNYeEigMzLlSWryR_eaMjHIFFkNFnPjrEJURx_hmSkX4FQFf-PX5df4em2f2ehwNRigAlgem8SfjdHez6iyplTdaFN_HG-9bZ7o"
API_BASE = "https://api.minimaxi.com/anthropic/v1"

payload = {
    "model": "MiniMax-M2",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.3,
    "max_tokens": 2000,
}
req = urllib.request.Request(
    f"{API_BASE}/messages",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    method="POST"
)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())
    for item in data.get("content", []):
        if item.get("type") == "text":
            return item["text"]
    return str(data.get("content", ""))
```

## 响应结构

```json
{
  "id": "0651cbb86533755b3a673675a3f42636",
  "type": "message",
  "role": "assistant",
  "model": "MiniMax-M2",
  "content": [
    {"type": "thinking", "thinking": "...", "signature": "..."},
    {"type": "text", "text": "今天阳光明媚..."}
  ],
  "usage": {"input_tokens": 46, "output_tokens": 50},
  "stop_reason": "max_tokens",
  "base_resp": {"status_code": 0, "status_msg": ""}
}
```

## 两个关键点

1. **`content` 是顶层字段**，不是 `choices[0].message.content`
2. **`content` 是 list**，有 `thinking` 和 `text` 两种 type，取 `text` 才是正文
