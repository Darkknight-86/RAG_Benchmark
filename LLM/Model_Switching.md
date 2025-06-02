# Model Switching in RAG System

This document outlines the model switching capabilities and configuration in our RAG system.

## Supported Models

The system currently supports the following model types:

1. **FLAN-T5 Models**
   - `google/flan-t5-small`
   - `google/flan-t5-base`
   - `google/flan-t5-large`

2. **Instruct Models**
   - `google/flan-t5-instruct`
   - `google/flan-t5-instruct-large`

## Environment Variables

### Required Variables
```bash
# Model Configuration
DEFAULT_LLM_MODEL=google/flan-t5-small  # Default model to use
DEFAULT_TEMPERATURE=0.7                  # Model temperature (0.0 to 1.0)
DEFAULT_MAX_TOKENS=200                   # Maximum tokens for generation
DEFAULT_TOP_K=5                          # Top-k sampling parameter

# API Keys (if using gated models)
HUGGINGFACE_API_KEY=your_api_key_here    # Required for gated models
```

### Optional Variables
```bash
# Model-specific configurations
SUPPORTED_MODELS=google/flan-t5-small,google/flan-t5-base,google/flan-t5-large  # Comma-separated list of supported models
```

## Model Configuration

The model configuration is managed through the `config.py` file, which includes:

1. **Default Parameters**:
   ```python
   MODEL_CONFIG = {
       "default_model": os.getenv("DEFAULT_LLM_MODEL", "google/flan-t5-small"),
       "default_temperature": float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
       "default_max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "200")),
       "default_top_k": int(os.getenv("DEFAULT_TOP_K", "5")),
       "supported_models": os.getenv("SUPPORTED_MODELS", "google/flan-t5-small,google/flan-t5-base,google/flan-t5-large").split(",")
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

The system uses different prompt templates based on the model type:

1. **FLAN-T5 Models**:
   ```python
   PROMPT_TEMPLATES["flan-t5"] = """
   Instruction: Using only the information in the context provided, respond to the question below.
   Do not include any outside knowledge or assumptions. If the answer cannot be found in the context, say "Not found in context."

   Context:
   {context}

   Question:
   {query}

   Answer:"""
   ```

2. **Instruct Models**:
   ```python
   PROMPT_TEMPLATES["instruct"] = """
   <s>[INST] <<SYS>>
   {system_prompt}
   <</SYS>>

   Instruction: Using only the information in the context provided, respond to the question below.
   Do not include any outside knowledge or assumptions. If the answer cannot be found in the context, say "Not found in context."

   Context:
   {context}

   Question:
   {query} [/INST]"""
   ```

## Switching Models

### Via Environment Variables

1. **Temporary Switch**:
   ```bash
   # Set for current session
   export DEFAULT_LLM_MODEL=google/flan-t5-base
   ```

2. **Permanent Switch**:
   ```bash
   # Add to .env file
   echo "DEFAULT_LLM_MODEL=google/flan-t5-base" >> .env
   ```

### Via Docker

1. **Using docker-compose**:
   ```yaml
   services:
     llm-service:
       environment:
         - DEFAULT_LLM_MODEL=google/flan-t5-base
         - DEFAULT_TEMPERATURE=0.7
         - DEFAULT_MAX_TOKENS=200
         - DEFAULT_TOP_K=5
   ```

2. **Using docker run**:
   ```bash
   docker run -e DEFAULT_LLM_MODEL=google/flan-t5-base \
              -e DEFAULT_TEMPERATURE=0.7 \
              -e DEFAULT_MAX_TOKENS=200 \
              -e DEFAULT_TOP_K=5 \
              llm-service
   ```

## Best Practices

1. **Model Selection**:
   - Use smaller models (e.g., `flan-t5-small`) for development and testing
   - Use larger models (e.g., `flan-t5-large`) for production when quality is critical
   - Consider using instruct models for more complex tasks

2. **Parameter Tuning**:
   - Start with default parameters
   - Adjust temperature based on response variability needs
   - Monitor token usage and adjust max_tokens accordingly
   - Use top_k to control response diversity

3. **Model Comparison**:
| Model              | Params | VRAM | First-query latency |
|--------------------|--------|------|--------------------|
| flan-t5-small      | 0.08 B | 1 GB | ~0.2 s             |
| flan-t5-base       | 0.25 B | 2 GB | ~0.4 s             |
| flan-t5-large      | 0.78 B | 8 GB | ~0.9 s             |
| mistral-7B-inst    | 7.0 B  | 13 GB| ~1.8 s             |
| llama-3-8B-inst    | 8.0 B  | 14 GB| ~2.0 s             |

4. **Resource Management**:
   - Monitor memory usage when switching to larger models
   - Consider model size when deploying to resource-constrained environments
   - Use appropriate batch sizes for your hardware

5. **Error Handling**:
   - Implement fallback to default model if specified model fails to load
   - Validate model parameters before initialization
   - Log model switching events for monitoring

## Troubleshooting

1. **Model Loading Issues**:
   ```bash
   # Check model availability
   curl -H "Authorization: Bearer $HUGGINGFACE_API_KEY" \
        https://huggingface.co/api/models/google/flan-t5-small
   ```

2. **Memory Issues**:
   ```bash
   # Monitor container memory usage
   docker stats llm-service
   ```

3. **Performance Issues**:
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

## Future Improvements

1. **Planned Features**:
   - Dynamic model switching based on load
   - Automatic model fallback
   - Model performance analytics
   - A/B testing support

2. **Potential Models**:
   - GPT-2 variants
   - BERT variants
   - Custom fine-tuned models