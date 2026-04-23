"""OpenAI SDK adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from luvoire.observability.tracing import genai_attributes, trace_span
from luvoire.protocols import Message


class OpenAIClient:
    """Thin OpenAI-compatible Responses API wrapper."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def complete(self, messages: Sequence[Message], **kwargs: Any) -> str:
        from openai import OpenAI

        temperature = float(kwargs.get("temperature", 0.7))
        max_tokens = int(kwargs.get("max_tokens", 1024))
        with trace_span(
            "luvoire.llm.openai.complete",
            genai_attributes(
                system="openai",
                operation="responses.create",
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=self.base_url,
            ),
        ) as span:
            client: Any = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.responses.create(
                model=self.model,
                input=[
                    {"role": message.get("role", "user"), "content": message.get("content", "")}
                    for message in messages
                ],
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            output = str(response.output_text).strip()
            if span is not None:
                span.set_attribute("luvoire.llm.response_length", len(output))
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "input_tokens", None)
                output_tokens = getattr(usage, "output_tokens", None)
                if isinstance(input_tokens, int):
                    span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
                if isinstance(output_tokens, int):
                    span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
            return output


__all__ = ["OpenAIClient"]
