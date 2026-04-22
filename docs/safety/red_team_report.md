# Red Team Safety Report

Phase 53 adds deterministic red-team checks for the public Luvoire safety boundary. The suite is intentionally local and replayable: it does not call external moderation APIs, and it does not claim to replace provider-side safety systems.

## Attack Vectors

| Vector | Test surface | Target | Result |
| --- | --- | ---: | --- |
| Prompt injection | 50 jailbreak, role override, hidden prompt, and policy leak attempts | 42 blocked | 50 blocked |
| Synthetic PII leakage | Synthetic SSN, payment card, email, and phone examples | 100% blocked | 100% blocked |
| Harmful content | Violence, harassment, self-harm, credential theft, and non-consensual content prompts | blocked | blocked |
| Scenario abuse | Prediction, suspect ranking, real-person profiling, and surveillance requests | 100% rejected | rejected by filter and DSL validator |
| Audit logging | JSONL append/read/validate round trip | schema valid | schema valid |

## Recommendations

- Keep the content filter opt-in and deterministic for CI.
- Use provider moderation for live LLM calls.
- Keep public-safety scenarios fictional, synthetic, non-identifying, and replay-only.
- Log blocked safety events with the JSONL audit schema when running demos or hosted services.
- Treat a red-team pass as a regression check, not as a production safety certification.
