# Local vs Cloud LLM Fallback Notes

Phase 36 adds local-server adapters for Ollama, llama.cpp, and vLLM. The benchmark below is a planning baseline, not a vendor claim. Re-run it on the target machine before making release or pricing claims.

| Path | Example model | Runtime surface | Cost shape | Expected strengths | Expected tradeoffs |
| --- | --- | --- | --- | --- | --- |
| Ollama | Llama 3.3, Gemma 3, Qwen 2.5 | `http://localhost:11434/api/chat` | local hardware, zero API calls | easiest developer setup, good demo fallback | depends on local memory and model pull size |
| llama.cpp server | GGUF quantized Llama/Gemma/Qwen | OpenAI-compatible `:8080/v1/chat/completions` | local CPU/GPU | small deployment footprint, quantized models | quality and latency vary by quantization |
| vLLM | Qwen 2.5 or Llama-class instruct model | OpenAI-compatible `:8000/v1/chat/completions` | local GPU server | high-throughput batching | operationally heavier, GPU recommended |
| Cloud provider | OpenAI/Anthropic | hosted API | per-token API cost | best availability and managed models | network dependency and variable token cost |

## Reproduction Checklist

1. Run the same prompt set through `LLMGateway` with cloud first and local fallback second.
2. Capture `LLMGateway.records` for provider, success, elapsed seconds, and estimated cost.
3. Repeat with local-first order when validating offline demos.
4. Record machine class, model name, quantization, context length, and server version.

## Safe Default

Keep cloud providers first for production-quality responses and local providers first for offline demos. Keep deterministic `LocalClient` last so notebooks and CI can run without a local model server.
