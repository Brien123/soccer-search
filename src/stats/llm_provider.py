import re
from typing import Any

import httpx

from stats.config import AppConfig


class LlmProvider:
    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._think_pattern: Any = re.compile(r"<think>.*?</think>", re.DOTALL)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self._config.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1000,
        }
        with httpx.Client(timeout=180.0) as client:
            response: httpx.Response = client.post(
                f"{self._config.llm_host}/chat/completions", json=payload
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        choices: list[Any] = data.get("choices", [])
        if not choices:
            raise RuntimeError("LLM returned no choices.")
        message: dict[str, Any] = choices[0].get("message", {})
        raw: str = str(message.get("content", ""))
        cleaned: str = self._think_pattern.sub("", raw).strip()
        if not cleaned:
            raise RuntimeError("LLM returned an empty answer.")
        return cleaned

    def model_name(self) -> str:
        return self._config.llm_model
