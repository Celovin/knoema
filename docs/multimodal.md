# Multimodal Voice Playback

Knoema's Playground can turn timeline `speak` actions into inline audio with OpenAI text-to-speech. Voice playback is opt-in, collapsed by default, and disabled until a user turns on the control in the timeline tab.

## Runtime Behavior

- `src/knoema/multimodal/tts.py` exposes `VoiceProfile` and `synthesize(text, profile)`.
- The Playground maps the first three timeline agents to per-agent voice pickers.
- Available OpenAI voices are `alloy`, `echo`, `fable`, `onyx`, `nova`, and `shimmer`; each picker also supports `mute`.
- Audio is rendered beside `speak` rows as inline WAV `<audio>` controls.
- Page load and normal replay runs do not call OpenAI while the voice toggle is off.
- Synthesis uses an on-disk cache keyed by `SHA256(text + serialized VoiceProfile)`, so repeated utterances for the same profile reuse cached WAV bytes.
- If `OPENAI_API_KEY` is unset, `synthesize` returns a deterministic short silent WAV. This keeps tests, local replay, and the HF Space smoke path functional without live TTS credentials.

## Cost Estimate

OpenAI's current model pages list TTS-1 at `$15` and TTS-1 HD at `$30` for speech generation per 1M units, and the API pricing page labels classic TTS billing in characters. For planning purposes, use the character-based estimate below and recheck the official pricing page before production demos.

| Knoema provider | OpenAI model | Voice tier | Voices | Estimate per 1K chars | Estimate per 1M chars |
| --- | --- | --- | --- | ---: | ---: |
| `openai` | `tts-1` | Standard | all six voices | `$0.015` | `$15.00` |
| `openai-hd` | `tts-1-hd` | HD | all six voices | `$0.030` | `$30.00` |
| `offline` | silent WAV fallback | Local fallback | n/a | `$0.000` | `$0.00` |

Sources checked on 2026-04-22: OpenAI model pages for `tts-1` and `tts-1-hd`, plus the OpenAI API pricing page.

## Privacy

When the voice toggle is enabled and a cache miss occurs, the text of the selected `speak` action is sent to OpenAI for speech generation. Do not enable voice playback for private, identifying, regulated, or third-party text unless the project has consent and an appropriate data-handling basis. Cached audio is stored locally under `KNOEMA_TTS_CACHE_DIR` when set, otherwise under the operating system temp directory.

The offline fallback does not send text to any external provider.
