"""Deterministic cache for recorded LLM side effects.

Cache keys are SHA256 digests over a canonical JSON request envelope:

- `model` is the provider model name as a string.
- `prompt_sha256` is the SHA256 digest of the UTF-8 prompt bytes.
- `sampling` is recursively normalized with mapping keys sorted alphabetically.
  Integers remain decimal JSON numbers, finite floats remain JSON numbers, bytes
  become hex strings, and unknown objects fall back to their string form.
- `seed` is stored as a decimal integer string.

The cache file is newline-delimited messagepack (NDMP). Each physical line is
base64-encoded messagepack so line framing is stable for streaming appends.
Line 0 is a header record. Every later line is an append-only record containing
at least `key` and `response`.
"""

from __future__ import annotations

import base64
import math
import os
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, BinaryIO, Literal, Self, cast

import msgpack  # type: ignore[import-untyped]

ReplayCacheMode = Literal["record", "replay", "off"]

FORMAT_NAME = "luvoire.replay_cache.v1"


class ReplayCacheError(RuntimeError):
    """Base error for replay-cache failures."""


class ReplayCacheMiss(ReplayCacheError):  # noqa: N818
    """Raised when replay mode cannot find a requested key."""


class ReplayCacheFormatError(ReplayCacheError):
    """Raised when an NDMP cache file is malformed."""


class ReplayCacheLockError(ReplayCacheError):
    """Raised when a second writer attempts to record to the same cache."""


@dataclass(frozen=True, slots=True)
class RecordedResponse:
    text: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    model_fingerprint: str | None
    captured_at: datetime

    def as_dict(self) -> dict[str, object]:
        captured_at = self.captured_at
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=UTC)
        else:
            captured_at = captured_at.astimezone(UTC)
        return {
            "text": self.text,
            "finish_reason": self.finish_reason,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "model_fingerprint": self.model_fingerprint,
            "captured_at": captured_at.isoformat().replace("+00:00", "Z"),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> Self:
        captured_raw = payload.get("captured_at")
        if not isinstance(captured_raw, str):
            raise ReplayCacheFormatError("recorded response is missing captured_at")
        captured_at = datetime.fromisoformat(captured_raw.replace("Z", "+00:00"))
        fingerprint = payload.get("model_fingerprint")
        if fingerprint is not None and not isinstance(fingerprint, str):
            raise ReplayCacheFormatError("model_fingerprint must be a string or null")
        return cls(
            text=str(payload.get("text", "")),
            finish_reason=str(payload.get("finish_reason", "")),
            prompt_tokens=_int_payload_field(payload, "prompt_tokens"),
            completion_tokens=_int_payload_field(payload, "completion_tokens"),
            model_fingerprint=fingerprint,
            captured_at=captured_at,
        )


@dataclass(frozen=True, slots=True)
class ReplayCacheSummary:
    record_count: int
    unique_models: tuple[str, ...]
    first_capture: str | None
    last_capture: str | None
    total_bytes: int

    def as_dict(self) -> dict[str, object]:
        return {
            "record_count": self.record_count,
            "unique_models": list(self.unique_models),
            "first_capture": self.first_capture,
            "last_capture": self.last_capture,
            "total_bytes": self.total_bytes,
        }


class ReplayCache:
    """Append-only deterministic cache of LLM request keys to recorded responses."""

    def __init__(self, path: Path, mode: ReplayCacheMode = "off") -> None:
        if mode not in {"record", "replay", "off"}:
            raise ValueError(f"unsupported replay cache mode: {mode}")
        self.path = Path(path)
        self.mode: ReplayCacheMode = mode
        self._records: dict[str, RecordedResponse] = {}
        self._models_by_key: dict[str, str] = {}
        self._append_file: BinaryIO | None = None
        self._lock_path: Path | None = None
        self._created_at: str | None = None

        if self.mode == "off":
            return
        if self.mode == "replay" and not self.path.exists():
            raise FileNotFoundError(f"replay cache does not exist: {self.path}")

        if self.mode == "record":
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._acquire_writer_lock()

        if self.path.exists() and self.path.stat().st_size > 0:
            self._load_records()
        elif self.mode == "record":
            self._created_at = _utc_now_iso()
            self._append_file = self.path.open("ab")
            self._write_line({"format": FORMAT_NAME, "created_at": self._created_at})

        if self.mode == "record" and self._append_file is None:
            self._append_file = self.path.open("ab")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def key(self, *, model: str, prompt: str, sampling: Mapping[str, Any], seed: int) -> str:
        """Canonicalize request inputs and return a stable SHA256 hex digest."""

        payload = {
            "model": str(model),
            "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
            "sampling": _canonical_value(sampling),
            "seed": str(int(seed)),
        }
        encoded = json_dumps(payload)
        digest = sha256(encoded.encode("utf-8")).hexdigest()
        self._models_by_key[digest] = str(model)
        return digest

    def get(self, key: str) -> RecordedResponse | None:
        if self.mode == "off":
            return None
        response = self._records.get(key)
        if response is None and self.mode == "replay":
            raise ReplayCacheMiss(f"replay cache miss for key {key}")
        return response

    def put(self, key: str, response: RecordedResponse) -> None:
        if self.mode == "off":
            return
        if self.mode != "record":
            raise ReplayCacheError("replay cache is not open in record mode")
        self._records[key] = response
        record: dict[str, object] = {"key": key, "response": response.as_dict()}
        model = self._models_by_key.get(key)
        if model is not None:
            record["model"] = model
        self._write_line(record)

    def close(self) -> None:
        if self._append_file is not None:
            self._append_file.flush()
            self._append_file.close()
            self._append_file = None
        if self._lock_path is not None:
            with suppress(FileNotFoundError):
                self._lock_path.unlink()
            self._lock_path = None

    def _acquire_writer_lock(self) -> None:
        lock_path = self.path.with_name(f"{self.path.name}.lock")
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ReplayCacheLockError(
                f"replay cache is already open for recording: {self.path}"
            ) from exc
        try:
            os.write(fd, f"{os.getpid()}\n".encode("ascii"))
        finally:
            os.close(fd)
        self._lock_path = lock_path

    def _load_records(self) -> None:
        with self.path.open("rb") as handle:
            for line_number, line in enumerate(handle):
                stripped = line.strip()
                if not stripped:
                    continue
                payload = _unpack_line(stripped)
                if line_number == 0:
                    if payload.get("format") != FORMAT_NAME:
                        raise ReplayCacheFormatError(
                            f"unsupported replay cache format in {self.path}"
                        )
                    created_at = payload.get("created_at")
                    self._created_at = str(created_at) if created_at is not None else None
                    continue
                key_raw = payload.get("key")
                response_raw = payload.get("response")
                if not isinstance(key_raw, str) or not isinstance(response_raw, Mapping):
                    raise ReplayCacheFormatError(
                        f"malformed replay cache record at line {line_number + 1}"
                    )
                self._records[key_raw] = RecordedResponse.from_dict(response_raw)
                model_raw = payload.get("model")
                if isinstance(model_raw, str):
                    self._models_by_key[key_raw] = model_raw

    def _write_line(self, payload: Mapping[str, object]) -> None:
        if self._append_file is None:
            raise ReplayCacheError("replay cache append file is not open")
        self._append_file.write(_pack_line(payload))
        self._append_file.flush()


def replay_cache_from_env() -> ReplayCache | None:
    path = os.environ.get("LUVOIRE_REPLAY_CACHE_PATH")
    if not path:
        return None
    mode_raw = os.environ.get("LUVOIRE_REPLAY_CACHE_MODE", "record").strip().lower()
    if mode_raw not in {"record", "replay", "off"}:
        raise ReplayCacheError(
            "LUVOIRE_REPLAY_CACHE_MODE must be one of: record, replay, off"
        )
    mode = cast(ReplayCacheMode, mode_raw)
    if mode == "off":
        return None
    return ReplayCache(Path(path), mode=mode)


def inspect_replay_cache(path: Path) -> ReplayCacheSummary:
    models: set[str] = set()
    captures: list[str] = []
    record_count = 0
    with Path(path).open("rb") as handle:
        for line_number, line in enumerate(handle):
            stripped = line.strip()
            if not stripped:
                continue
            payload = _unpack_line(stripped)
            if line_number == 0:
                if payload.get("format") != FORMAT_NAME:
                    raise ReplayCacheFormatError(f"unsupported replay cache format in {path}")
                continue
            response_raw = payload.get("response")
            if not isinstance(response_raw, Mapping):
                raise ReplayCacheFormatError(
                    f"malformed replay cache record at line {line_number + 1}"
                )
            record_count += 1
            model_raw = payload.get("model")
            models.add(model_raw if isinstance(model_raw, str) else "unknown")
            captured_raw = response_raw.get("captured_at")
            if isinstance(captured_raw, str):
                captures.append(captured_raw)
    captures.sort()
    return ReplayCacheSummary(
        record_count=record_count,
        unique_models=tuple(sorted(models)),
        first_capture=captures[0] if captures else None,
        last_capture=captures[-1] if captures else None,
        total_bytes=Path(path).stat().st_size,
    )


def json_dumps(payload: Mapping[str, object]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _canonical_value(value: Any) -> object:
    if value is None or isinstance(value, str | bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("sampling floats must be finite")
        return value
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_canonical_value(item) for item in value]
    return str(value)


def _pack_line(payload: Mapping[str, object]) -> bytes:
    packed = msgpack.packb(dict(payload), use_bin_type=True)
    return base64.b64encode(packed) + b"\n"


def _unpack_line(line: bytes) -> dict[str, Any]:
    try:
        decoded = base64.b64decode(line, validate=True)
        payload = msgpack.unpackb(decoded, raw=False)
    except Exception as exc:
        raise ReplayCacheFormatError("invalid replay cache line") from exc
    if not isinstance(payload, dict):
        raise ReplayCacheFormatError("replay cache line must decode to a mapping")
    return payload


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _int_payload_field(payload: Mapping[str, object], name: str) -> int:
    value = payload.get(name, 0)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    raise ReplayCacheFormatError(f"{name} must be numeric")


__all__ = [
    "FORMAT_NAME",
    "RecordedResponse",
    "ReplayCache",
    "ReplayCacheError",
    "ReplayCacheFormatError",
    "ReplayCacheLockError",
    "ReplayCacheMiss",
    "ReplayCacheMode",
    "ReplayCacheSummary",
    "inspect_replay_cache",
    "replay_cache_from_env",
]
