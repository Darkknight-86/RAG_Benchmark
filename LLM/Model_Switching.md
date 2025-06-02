# Plug-and-Play Model Switching for the LLM Service

This short guide explains **how to change the Hugging Face model** that the
`llm` micro-service loads at runtime, without touching any other
micro-services in the RAG stack.

---

## 1. Quick Start — one-liner

Set an environment variable and restart the container:

```bash
# choose any public Hugging Face repo ID
export DEFAULT_LLM_MODEL=google/flan-t5-large

# rebuild only if you want the layer cached, otherwise just restart
docker compose up -d --no-deps --build llm
```

The service looks for the variable in `LLMManager`:

```python
self.default_model = os.getenv("DEFAULT_LLM_MODEL", "google/flan-t5-large")
```

If the env-var is unset, it falls back to the baked-in default.

---

## 2. Permanent change via `docker-compose.yml`

```yaml
services:
  llm:
    build:
      context: .
      dockerfile: LLM/RAG/Dockerfile
    environment:
      - DEFAULT_LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
```

Re-create the container:

```bash
docker compose up -d --no-deps llm
```

---

## 3. Supported model types

| Family                 | HF repo example                                   | Notes                                  |
|------------------------|----------------------------------------------------|----------------------------------------|
| Flan-T5                | `google/flan-t5-large`                             | Seq2Seq; good zero-shot QA            |
| Mistral-7B-Instruct    | `mistralai/Mistral-7B-Instruct-v0.2`               | Causal LM; add `[INST]` wrappers      |
| Llama-3-8B-Instruct    | `meta-llama/Meta-Llama-3-8B-Instruct`              | License acceptance required            |
| Any GGUF quantised     | `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`           | Use llama-cpp loader instead (TODO)    |

The loader first tries `AutoModelForCausalLM`; if that fails it falls
back to `AutoModelForSeq2SeqLM`, so most encoder-decoder checkpoints
(e.g. Flan-T5) still work.

---

## 4. Memory & speed cheat-sheet (FP16)

| Model              | Params | VRAM | First-query latency |
|--------------------|--------|------|--------------------|
| flan-t5-base       | 0.25 B | 2 GB | ~0.4 s             |
| flan-t5-large      | 0.78 B | 8 GB | ~0.9 s             |
| mistral-7B-inst    | 7.0 B  | 13 GB| ~1.8 s             |
| llama-3-8B-inst    | 8.0 B  | 14 GB| ~2.0 s             |

_To fit larger models on 8 GB cards use 8-bit or 4-bit loading:_

```python
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    load_in_8bit=True,
    device_map="auto"
)
```

---

## 5. Prompt wrapping rules

The LLM manager auto-detects "Instruct" models and wraps the prompt:

```python
if "instruct" in model_name.lower():
    prompt = f"<s>[INST] {prompt} [/INST]"
```

For other models (Flan-T5, GPT-J, etc.) no wrapper is applied—provide an
instructional prompt directly.

---

## 6. Cache location

Downloaded weights are stored in the container layer under
`~/.cache/huggingface/hub`.  Rebuild once to bake them into the image; later
restarts are instant.

---

Feel free to extend this doc when you add new loaders (e.g. llama-cpp
for GGUF, vLLM, TensorRT-LLM).