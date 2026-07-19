#!/usr/bin/env python3
"""Read COROS heart-rate/pace zone chart via OpenRouter vision.

Usage:
    python3 coros_zone_reader.py [/path/to/coros_screenshot.jpg] ["custom prompt"]

Prompts the user to describe the chart in Chinese. Reads OPENROUTER_API_KEY
from ~/.hermes/.env.
"""

import sys
import base64
import os
from pathlib import Path


def _load_or_key() -> str:
    """Read OPENROUTER_API_KEY from ~/.hermes/.env, bypassing Hermes masking."""
    env_path = Path.home() / ".hermes" / ".env"
    key = None
    for line in env_path.read_text().splitlines():
        if "OPENROUTER_API_KEY" in line:
            key = line.split("=", 1)[1].strip()
            break
    if not key:
        print("ERROR: OPENROUTER_API_KEY not found in ~/.hermes/.env", file=sys.stderr)
        sys.exit(1)
    return key


def analyze_coros_chart(image_path: str, prompt: str = None) -> str:
    """Send a COROS zone chart to GPT-4o vision and return the description."""
    key = _load_or_key()
    if prompt is None:
        prompt = (
            "Read the COROS watch 'Lactate Threshold Heart Rate / Pace Zone' "
            "chart in this image. List: LTHR bpm, Max HR, Resting HR, "
            "threshold pace, and all 6 zones with their HR ranges and pace ranges."
        )

    from openai import OpenAI
    client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    resp = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        max_tokens=500,
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    img = sys.argv[1] if len(sys.argv) > 1 else None
    prompt = sys.argv[2] if len(sys.argv) > 2 else None
    if img:
        result = analyze_coros_chart(img, prompt)
        print(result)
    else:
        print(__doc__)
