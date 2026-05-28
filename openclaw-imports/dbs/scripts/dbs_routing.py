#!/usr/bin/env python3
"""
dbs_routing.py — dontbesilent 商业工具箱路由脚本

根据用户输入的关键词，输出建议的 skill 名称。
用法：
  python dbs_routing.py <用户输入文本>
"""

import sys
import re

ROUTING_RULES = [
    # (关键词列表, 目标skill, 优先级)
    (["拖延", "知道该做", "就是不做", "执行力", "做不动", "action"], "dbs-action", 10),
    (["商业模式", "商业问题", "赚钱", "诊断", "business", "diagnosis"], "dbs-diagnosis", 9),
    (["对标", "学谁", "模仿", "benchmark"], "dbs-benchmark", 9),
    (["内容", "选题", "内容怎么做", "content"], "dbs-content", 9),
    (["开头", "hook", "视频文案", "短视频"], "dbs-hook", 9),
    (["标题", "小红书", "xhs", "title"], "dbs-xhs-title", 9),
    (["ai味", "ai味检测", "ai味太重", "检测一下"], "dbs-ai-check", 9),
    (["慢", "快方法", "捷径", "slowisfast", "更慢"], "dbs-slowisfast", 8),
    (["概念", "拆解", "什么意思", "deconstruct"], "dbs-deconstruct", 9),
    (["chatroom", "聊天室", "多视角", "讨论", "专家"], "dbs-chatroom", 7),
    (["agent", "迁移", "claude code", "codex", "agents.md", "工作台"], "dbs-agent-migration", 10),
    (["奥派", "哈耶克", "米塞斯", "austrian"], "dbs-chatroom-austrian", 8),
]

def route(text: str) -> list[tuple[str, int]]:
    text_lower = text.lower()
    results = []
    for keywords, skill, priority in ROUTING_RULES:
        for kw in keywords:
            if kw.lower() in text_lower:
                results.append((skill, priority))
                break
    results.sort(key=lambda x: -x[1])
    seen = []
    for skill, _ in results:
        if skill not in seen:
            seen.append(skill)
    return seen

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python dbs_routing.py <用户输入文本>")
        sys.exit(1)
    text = " ".join(sys.argv[1:])
    matches = route(text)
    if matches:
        print(f"建议路由到: {matches[0]}")
        if len(matches) > 1:
            print(f"其他可能: {', '.join(matches[1:])}")
    else:
        print("未匹配到明确路由，请使用 /dbs 交互式选择")