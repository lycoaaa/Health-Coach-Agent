from __future__ import annotations
import os, json, requests, time
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

DEESEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL    = "deepseek-chat"        # 可以使用reasoner

_API_KEY_ENV = "DEEPSEEK_API_KEY"         # 写到 .env / shell 里：export DEEPSEEK_API_KEY=xxx

class DeepSeekError(RuntimeError):
    ...

def _build_messages(prompt: str, system: str | None = None) -> List[Dict]:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs

def call_local_llm(
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        timeout: int = 60,
) -> str:

    api_key = os.getenv(_API_KEY_ENV)
    if not api_key:
        raise DeepSeekError(f"环境变量 {_API_KEY_ENV} 未设置")

    payload = {
        "model": model,
        "temperature": temperature,
        "stream": False,
        "messages": _build_messages(prompt, system_prompt),
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    t0 = time.time()
    resp = requests.post(
        DEESEEK_ENDPOINT,
        headers=headers,
        data=json.dumps(payload),
        timeout=timeout,
    )
    latency = time.time() - t0

    if resp.status_code != 200:
        raise DeepSeekError(
            f"DeepSeek API {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    print(f"DeepSeek {model} {len(prompt)}→{len(content)} tokens, "
          f"{latency*1000:.0f} ms")

    return content.strip()
