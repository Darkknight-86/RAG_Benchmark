# Model Switching in RAG System

This document explains how to switch between different models in our RAG system.

## Supported Models

The system currently supports these Llama models:

1. **Llama 3.2 Models**
   - `meta-llama/Llama-3.2-1B-Instruct` (default)
   - `meta-llama/Llama-3.2-3B-Instruct`

## Environment Variables

### Required Variables
```bash
# Model Configuration
DEFAULT_LLM_MODEL=meta-llama/Llama-3.2-1B-Instruct  # Default model to use
DEFAULT_TEMPERATURE=0.7                              # Model temperature (0.0 to 1.0)
DEFAULT_MAX_TOKENS=1000                              # Maximum tokens for generation
DEFAULT_TOP_K=5                                      # Top-k sampling parameter

# API Keys (required for Llama models)
HUGGINGFACE_HUB_TOKEN=your_token_here               # Required for Llama models
```

### Optional Variables
```bash
# Model-specific configurations
SUPPORTED_MODELS=meta-llama/Llama-3.2-1B-Instruct,meta-llama/Llama-3.2-3B-Instruct  # Comma-separated list
```

## Model Configuration

The model configuration is managed through the `config.py` file, which includes:

1. **Default Parameters**:
   ```python
   MODEL_CONFIG = {
       "default_model": os.getenv("DEFAULT_LLM_MODEL", "meta-llama/Llama-3.2-1B-Instruct"),
       "default_temperature": float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
       "default_max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "1000")),
       "default_top_k": int(os.getenv("DEFAULT_TOP_K", "5")),
       "supported_models": os.getenv("SUPPORTED_MODELS", "meta-llama/Llama-3.2-1B-Instruct,meta-llama/Llama-3.2-3B-Instruct").split(",")
   }
   ```

2. **Parameter Validation**:
   ```python
   def validate_parameters(temperature: float, max_tokens: int, top_k: int) -> None:
       if not 0 <= temperature <= 1:
           raise ValueError("Temperature must be between 0 and 1")
       if max_tokens <= 0:
           raise ValueError("max_tokens must be positive")
       if top_k <= 0:
           raise ValueError("top_k must be positive")
   ```

## Model-Specific Prompts

The system uses Llama-specific prompt templates:

**Llama Models**:
```python
PROMPT_TEMPLATES["llama"] = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful financial AI assistant that answers questions based only on the provided context. Analyze the context carefully and provide detailed, accurate responses. If the answer cannot be found in the context, say "Not found in context."<|eot_id|><|start_header_id|>user<|end_header_id|>

Context:
{context}

Question: {query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
```

## Switching Models

### Via Environment Variables

1. **Temporary Switch**:
   ```bash
   # Set for current session
   export DEFAULT_LLM_MODEL=meta-llama/Llama-3.2-3B-Instruct
   ```

2. **Permanent Switch**:
   ```bash
   # Add to .env file
   echo "DEFAULT_LLM_MODEL=meta-llama/Llama-3.2-3B-Instruct" >> .env
   ```

### Via Docker

1. **Using docker-compose**:
   ```yaml
   services:
     llm-service:
       environment:
         - DEFAULT_LLM_MODEL=meta-llama/Llama-3.2-3B-Instruct
         - DEFAULT_TEMPERATURE=0.7
         - DEFAULT_MAX_TOKENS=1000
         - DEFAULT_TOP_K=5
         - HUGGINGFACE_HUB_TOKEN=${HUGGINGFACE_HUB_TOKEN}
   ```

2. **Using docker run**:
   ```bash
   docker run -e DEFAULT_LLM_MODEL=meta-llama/Llama-3.2-3B-Instruct \
              -e DEFAULT_TEMPERATURE=0.7 \
              -e DEFAULT_MAX_TOKENS=1000 \
              -e DEFAULT_TOP_K=5 \
              -e HUGGINGFACE_HUB_TOKEN=$HUGGINGFACE_HUB_TOKEN \
              llm-service
   ```

## Tips and Guidelines

1. **Model Selection**:
   - Use `Llama-3.2-1B-Instruct` for development and testing (faster, less memory)
   - Use `Llama-3.2-3B-Instruct` when you need better quality (slower, more memory)

2. **Parameter Tuning**:
   - Start with default parameters
   - Adjust temperature based on how creative you want responses to be
   - Monitor token usage and adjust max_tokens accordingly
   - Use top_k to control response diversity

3. **Model Comparison**:
| Model                          | Params | VRAM | First-query latency | Notes |
|--------------------------------|--------|------|--------------------| ------|
| Llama-3.2-1B-Instruct         | 1.2B   | 3 GB | ~0.5-1.0s          | Fast, good for testing |
| Llama-3.2-3B-Instruct         | 3.2B   | 7 GB | ~1.0-2.0s          | Better quality |

4. **Resource Management**:
   - Monitor memory usage when switching to larger models
   - Llama models require more memory than older models
   - Consider CPU vs GPU deployment

5. **Authentication**:
   - Llama models require HuggingFace authentication
   - Make sure `HUGGINGFACE_HUB_TOKEN` is set
   - Token needs access to Meta Llama models

## Quantization Options (Not Currently Used)

To enable quantization for better memory efficiency, you could add:

```python
# In llm_manager.py, add to model_kwargs:
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

model_kwargs = {
    'quantization_config': quantization_config,
    'torch_dtype': torch.float16,  # Instead of float32
    'device_map': "auto",
    **auth_kwargs
}
```

## Troubleshooting

1. **Model Loading Issues**:
   ```bash
   # Check model availability and token access
   curl -H "Authorization: Bearer $HUGGINGFACE_HUB_TOKEN" \
        https://huggingface.co/api/models/meta-llama/Llama-3.2-1B-Instruct
   ```

2. **Memory Issues**:
   ```bash
   # Monitor container memory usage
   docker stats llm-service
   ```

3. **Authentication Issues**:
   ```bash
   # Test HuggingFace token
   huggingface-cli whoami
   ```

4. **Performance Issues**:
   ```bash
   # Check model inference time
   docker logs llm-service | grep "inference_time"
   ```

## Monitoring

1. **Model Metrics**:
   - Inference time
   - Memory usage
   - Token usage
   - Response quality

2. **System Metrics**:
   - CPU utilization
   - Memory utilization
   - GPU utilization (if applicable)
   - Network I/O

## Future Ideas

1. **Planned Features**:
   - Dynamic model switching based on load
   - Automatic model fallback
   - Model performance analytics
   - A/B testing support
   - Quantization support for memory efficiency

2. **Potential Models**:
   - Llama-3.2-8B-Instruct (if more resources available)
   - Code Llama variants for technical queries
   - Custom fine-tuned Llama models