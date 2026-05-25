"""Provider-agnostic LLM client with fallback."""
from __future__ import annotations

import json
import logging
from typing import Any

from flask import current_app
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class BaseProvider:
    name: str = ""

    def call(self, system: str, user: str, *, json_mode: bool = True,
             max_tokens: int = 4000) -> tuple[str, int, int]:
        raise NotImplementedError


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def call(self, system, user, *, json_mode=True, max_tokens=4000):
        import anthropic
        key = current_app.config.get("ANTHROPIC_API_KEY")
        if not key:
            raise LLMError("no anthropic key")
        client = anthropic.Anthropic(api_key=key, timeout=current_app.config["AI_REQUEST_TIMEOUT"])
        model = current_app.config["AI_MODEL_ANTHROPIC"]
        if json_mode:
            system = system + "\n\n请仅返回严格的 JSON，不要包含 markdown 围栏。"
        resp = client.messages.create(
            model=model,
            system=system,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text"))
        in_t = getattr(resp.usage, "input_tokens", 0)
        out_t = getattr(resp.usage, "output_tokens", 0)
        return text, in_t, out_t


class OpenAIProvider(BaseProvider):
    name = "openai"

    def call(self, system, user, *, json_mode=True, max_tokens=4000):
        from openai import OpenAI
        key = current_app.config.get("OPENAI_API_KEY")
        if not key:
            raise LLMError("no openai key")
        base = current_app.config.get("OPENAI_BASE_URL") or None
        client = OpenAI(api_key=key, base_url=base, timeout=current_app.config["AI_REQUEST_TIMEOUT"])
        model = current_app.config["AI_MODEL_OPENAI"]
        kw: dict[str, Any] = dict(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=max_tokens,
        )
        if json_mode:
            kw["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kw)
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        return text, getattr(usage, "prompt_tokens", 0), getattr(usage, "completion_tokens", 0)


class DeepseekProvider(BaseProvider):
    name = "deepseek"

    def call(self, system, user, *, json_mode=True, max_tokens=4000):
        from openai import OpenAI
        key = current_app.config.get("DEEPSEEK_API_KEY")
        if not key:
            raise LLMError("no deepseek key")
        base = current_app.config.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
        client = OpenAI(api_key=key, base_url=base, timeout=current_app.config["AI_REQUEST_TIMEOUT"])
        model = current_app.config["AI_MODEL_DEEPSEEK"]
        kw: dict[str, Any] = dict(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=max_tokens,
        )
        if json_mode:
            kw["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kw)
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        return text, getattr(usage, "prompt_tokens", 0), getattr(usage, "completion_tokens", 0)


class DashscopeProvider(BaseProvider):
    name = "dashscope"

    def call(self, system, user, *, json_mode=True, max_tokens=4000):
        import dashscope
        key = current_app.config.get("DASHSCOPE_API_KEY")
        if not key:
            raise LLMError("no dashscope key")
        dashscope.api_key = key
        model = current_app.config["AI_MODEL_DASHSCOPE"]
        if json_mode:
            system = system + "\n\n请仅返回严格的 JSON，不要包含 markdown 围栏。"
        resp = dashscope.Generation.call(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            result_format="message",
            max_tokens=max_tokens,
        )
        if resp.status_code != 200:
            raise LLMError(f"dashscope error: {resp.message}")
        text = resp.output.choices[0].message.content
        return text, resp.usage.input_tokens, resp.usage.output_tokens


PROVIDERS: dict[str, type[BaseProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "deepseek": DeepseekProvider,
    "dashscope": DashscopeProvider,
}


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _try_provider(name: str, system: str, user: str, json_mode: bool, max_tokens: int):
    cls = PROVIDERS.get(name)
    if not cls:
        raise LLMError(f"unknown provider {name}")
    return cls().call(system, user, json_mode=json_mode, max_tokens=max_tokens)


def call_llm(system: str, user: str, *, json_mode: bool = True,
             max_tokens: int = 4000) -> tuple[str, int, int, str]:
    """Return (text, tokens_in, tokens_out, provider_used)."""
    primary = current_app.config["AI_PROVIDER"]
    fallback = [p.strip() for p in current_app.config.get("AI_PROVIDER_FALLBACK", []) if p.strip()]
    order = [primary] + [p for p in fallback if p != primary]
    last_err: Exception | None = None
    for p in order:
        try:
            text, ti, to = _try_provider(p, system, user, json_mode, max_tokens)
            return text, ti, to, p
        except Exception as e:
            log.warning("LLM provider %s failed: %s", p, e)
            last_err = e
    raise LLMError(f"All providers failed: {last_err}")


def parse_json(text: str) -> dict:
    """Best-effort JSON extraction from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    # Find first {
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)
