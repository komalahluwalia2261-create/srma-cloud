"""
Model-agnostic call layer.

The pipeline should be able to swap the underlying LLM without touching
ingestion, adapters, or prompt construction — this is what lets the paper
report cross-model robustness (a reviewer's first question after any single-
model screening result is "does this hold up on a different model?").

Add a new backend by implementing `ModelClient` and registering it in
`get_client()`. Only a stdlib-and-`requests`-level interface is assumed here
so backends stay swappable without pulling in every vendor SDK by default.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelResponse:
    raw_text: str
    model_name: str


class ModelClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 1024) -> ModelResponse:
        ...


class AnthropicClient(ModelClient):
    def __init__(self, model: str = "claude-sonnet-4-6", api_key_env: str = "ANTHROPIC_API_KEY"):
        import os
        import anthropic

        self._model = model
        self._client = anthropic.Anthropic(api_key=os.environ[api_key_env])

    def complete(self, prompt: str, max_tokens: int = 1024) -> ModelResponse:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return ModelResponse(raw_text=text, model_name=self._model)


class OpenAIClient(ModelClient):
    def __init__(self, model: str = "gpt-4o", api_key_env: str = "OPENAI_API_KEY"):
        import os
        from openai import OpenAI

        self._model = model
        self._client = OpenAI(api_key=os.environ[api_key_env])

    def complete(self, prompt: str, max_tokens: int = 1024) -> ModelResponse:
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return ModelResponse(raw_text=resp.choices[0].message.content, model_name=self._model)


def get_client(backend: str, **kwargs) -> ModelClient:
    registry = {
        "anthropic": AnthropicClient,
        "openai": OpenAIClient,
    }
    if backend not in registry:
        raise ValueError(f"Unknown model backend '{backend}'. Options: {list(registry)}")
    return registry[backend](**kwargs)


_DECISION_RE = re.compile(r"DECISION:\s*(INCLUDE|EXCLUDE|UNCERTAIN)", re.IGNORECASE)


def extract_decision(raw_text: str) -> tuple[str, str]:
    """Returns (decision, rationale). decision is lowercase include/exclude/uncertain."""
    match = _DECISION_RE.search(raw_text)
    decision = match.group(1).lower() if match else "uncertain"
    rationale = raw_text.strip()
    return decision, rationale
