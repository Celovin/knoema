"""Round-5 audit: provider exception messages must be scrubbed of
credential-looking substrings before they land in ``LLMCallRecord.error``.

Some provider SDKs (litellm, openai, anthropic) include the offending
API key inside ``AuthenticationError`` strings. Without redaction, those
strings reach observability backends and log shippers verbatim — a
single grep is then enough to harvest live keys from a debug dump.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from luvoire.llm.gateway import LLMGateway, _redact_secrets
from luvoire.protocols import Message


class _FailingClient:
    def __init__(self, *, model: str, exc_message: str) -> None:
        self.model = model
        self._exc_message = exc_message

    def complete(self, _messages: Sequence[Message], **_kwargs: Any) -> str:
        raise RuntimeError(self._exc_message)


@pytest.mark.parametrize(
    "raw_message,expected_substring",
    [
        # OpenAI-style sk-* key
        (
            "AuthenticationError: invalid api key sk-proj-1234567890abcdefghij",
            "***",
        ),
        # Stripe-style live key
        (
            "Bad request: sk_live_AbCdEf0123456789xyz",
            "***",
        ),
        # Luvoire tenant token
        (
            "401 forbidden: token=luvoire_ak0123456789ab_RawSecretBlobBase64",
            "***",
        ),
        # Bearer header
        (
            "rejected: Authorization: Bearer Hd92aJK3lmNoPqRs1234abcd",
            "***",
        ),
    ],
)
def test_redact_secrets_scrubs_known_credential_patterns(
    raw_message: str, expected_substring: str
) -> None:
    redacted = _redact_secrets(raw_message)
    assert expected_substring in redacted
    # The original credential MUST NOT appear in the redacted output.
    for token in raw_message.split():
        if token.startswith(("sk-", "sk_", "luvoire_ak")):
            assert token not in redacted, f"unredacted credential leaked: {token!r}"


def test_redact_secrets_preserves_non_credential_text() -> None:
    msg = "rate limit exceeded: 429 Too Many Requests, retry after 30s"
    assert _redact_secrets(msg) == msg


def test_redact_secrets_handles_multiple_credentials_in_one_message() -> None:
    msg = "key1=sk-proj-AAAAAAAAAAAAAAAA key2=sk_live_BBBBBBBBBBBBBBBB done"
    redacted = _redact_secrets(msg)
    assert "sk-proj-AAAAAAAAAAAAAAAA" not in redacted
    assert "sk_live_BBBBBBBBBBBBBBBB" not in redacted
    assert redacted.count("***") == 2


def test_gateway_records_redacted_error_after_provider_failure() -> None:
    """End-to-end: a provider raising with a credential in its message
    must NOT result in that credential landing in ``records[i].error``.
    """

    leaky_message = "401: invalid api key sk-proj-LIVEKEY1234567890abcdef"
    failing = _FailingClient(model="m", exc_message=leaky_message)
    succeeding = _FailingClient(model="m2", exc_message="ok")  # also fails so we see record
    gateway = LLMGateway(
        [("p1", failing), ("p2", succeeding)],
        fallback_deadline_seconds=10.0,
    )
    with pytest.raises(RuntimeError):
        gateway.complete([{"role": "user", "content": "hi"}])

    error_strings = [r.error for r in gateway.records if r.error is not None]
    assert error_strings, "expected at least one failed call recorded"
    for err in error_strings:
        assert "sk-proj-LIVEKEY1234567890abcdef" not in err, (
            f"credential leaked into LLMCallRecord.error: {err!r}"
        )
