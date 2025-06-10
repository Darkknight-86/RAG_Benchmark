from typing import Dict, Optional, Tuple
import time
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from dotenv import load_dotenv
import os
from config import MODEL_CONFIG, validate_parameters
from prompt_manager import prompt_manager

load_dotenv()

class LLMManager:
    """Manages different LLM models from Hugging Face."""

    def __init__(self):
        self.models: Dict[str, Tuple[AutoModelForCausalLM, AutoTokenizer]] = {}
        self.default_model = MODEL_CONFIG["default_model"]
        # Check for Apple Silicon MPS, then CUDA, then fallback to CPU
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        # Get Hugging Face token for gated models
        self.hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if self.hf_token:
            print("🔑 Using Hugging Face authentication token")
        else:
            print("⚠️ No Hugging Face token found - some models may not be accessible")
        if self.device == "mps":
            print(f"🚀 Using Apple Silicon GPU (MPS): {self.device}")
        elif self.device == "cuda":
            print(f"🚀 Using NVIDIA GPU (CUDA): {self.device}")
        else:
            print(f"💻 Using CPU: {self.device}")

    def load_model(self, model_name: str) -> None:
        """Load a model from Hugging Face."""
        if model_name in self.models:
            return

        if model_name not in MODEL_CONFIG["supported_models"]:
            raise ValueError(f"Model {model_name} is not in supported models list")

        print(f"Loading model: {model_name}")

        # Prepare authentication arguments
        auth_kwargs = {}
        if self.hf_token:
            auth_kwargs['token'] = self.hf_token

        # Load tokenizer with authentication
        tokenizer = AutoTokenizer.from_pretrained(model_name, **auth_kwargs)

        # Set padding token to avoid torch.isin MPS issues - use a different token than eos_token
        if tokenizer.pad_token is None:
            # Add a special pad token that's different from eos_token to avoid torch.isin comparison
            tokenizer.add_special_tokens({'pad_token': '<PAD>'})

        # Use device_map for CUDA, manual placement for MPS and CPU
        if self.device == "cuda":
            device_map_arg = "auto"
        else:
            device_map_arg = None  # Manual placement for MPS and CPU

                # Load model config with rope_scaling compatibility fix for transformers 4.41.0
        from transformers import AutoConfig
        from transformers.models.llama.configuration_llama import LlamaConfig

        # Temporarily disable rope_scaling validation to allow Llama 3.2 configs to load
        original_validation = LlamaConfig._rope_scaling_validation

        def patched_validation(self):
            """Patched validation that converts Llama 3.2 rope_scaling to 4.41.0 format"""
            if self.rope_scaling is not None:
                if isinstance(self.rope_scaling, dict) and 'rope_type' in self.rope_scaling:
                    if self.rope_scaling['rope_type'] == 'llama3':
                        # Convert llama3 rope_scaling to linear format compatible with 4.41.0
                        factor = self.rope_scaling.get('factor', 1.0)
                        self.rope_scaling = {'type': 'linear', 'factor': factor}
                        print(f"🔧 Fixed rope_scaling for MPS compatibility: {self.rope_scaling}")
                        return  # Skip the original validation
            # Call original validation for other cases
            original_validation(self)

        try:
            # Monkey patch the validation method
            LlamaConfig._rope_scaling_validation = patched_validation

            # Load config with patched validation
            config = AutoConfig.from_pretrained(model_name, **auth_kwargs)

        finally:
            # Always restore the original validation method
            LlamaConfig._rope_scaling_validation = original_validation

        # Optimized model loading arguments for MPS - float16 works with PyTorch 2.3.0 + transformers 4.41.0
        model_kwargs = {
            'config': config,  # Use the fixed config
            'torch_dtype': torch.float16,  # float16 for optimal MPS performance with PyTorch 2.3.0
            'device_map': device_map_arg,
            'low_cpu_mem_usage': True,
            **auth_kwargs  # Include authentication
        }

        # Try loading as causal LM (Llama models)
        try:
            model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
            print(f"✅ Loaded Llama model: {model_name}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise e

        # Move model to device if not using device_map
        if device_map_arg is None:
            model = model.to(self.device)

        # Resize model embeddings if we added a new pad token
        if tokenizer.pad_token == '<PAD>':
            model.resize_token_embeddings(len(tokenizer))

        self.models[model_name] = (model, tokenizer)
        print(f"Model loaded successfully on {self.device}")

    def get_model(self, model_name: Optional[str] = None) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """Get a loaded model or load it if not already loaded."""
        model_name = model_name or self.default_model
        if model_name not in self.models:
            self.load_model(model_name)
        return self.models[model_name]

    def generate_response(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        max_tokens: int = MODEL_CONFIG["default_max_tokens"],
        temperature: float = MODEL_CONFIG["default_temperature"],
        top_k: int = MODEL_CONFIG["default_top_k"]
    ) -> Tuple[str, float, int]:
        """Generate a response from the model."""
        # Ensure model_name is set
        model_name = model_name or self.default_model
        print(f"Generating response with model: {model_name}")

        # Validate parameters
        validate_parameters(temperature, max_tokens, top_k)

        # Validate and format prompt
        prompt_manager.validate_query(prompt)
        formatted_prompt = prompt_manager.format_prompt(prompt, [], model_name)  # Pass empty context list for now

        model, tokenizer = self.get_model(model_name)

        # Tokenize and generate with explicit attention_mask to avoid torch.isin MPS issues
        start_time = time.time()
        inputs = tokenizer(formatted_prompt, return_tensors="pt", padding=True, truncation=True)

        # Move inputs to the same device as the model
        if hasattr(model, 'device'):
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        else:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Ensure we have attention_mask to prevent torch.isin comparison
        if 'attention_mask' not in inputs:
            inputs['attention_mask'] = torch.ones_like(inputs['input_ids'])

        # Get model requirements
        model_reqs = prompt_manager.get_model_requirements(model_name)

        # Conservative generation parameters to prevent loops
        gen_kwargs = {
            "temperature": min(temperature, 0.7),  # Cap temperature
            "do_sample": temperature > 0.0,
            "num_beams": 1,
            "top_k": min(top_k, 50),  # Limit top_k
            "top_p": 0.9,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
            "use_cache": True,
            "return_dict_in_generate": False,
            # Add strict stopping criteria
            "repetition_penalty": 1.2,  # Prevent repetitive output
            "length_penalty": 1.0,
            "early_stopping": True,
            "max_new_tokens": min(max_tokens, 150)  # Hard cap on new tokens
        }

        # Generate with Causal LM (Llama models)
        # max_new_tokens is already in gen_kwargs to prevent token loops
        outputs = model.generate(
            **inputs,
            **gen_kwargs
        )

        # Extract only the newly generated tokens (not the input prompt)
        input_length = inputs['input_ids'].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = tokenizer.decode(generated_tokens, skip_special_tokens=True)

        # Calculate metrics
        latency = time.time() - start_time
        tokens_used = len(outputs[0])

        return response, latency, tokens_used

    def generate_response_raw(
        self,
        raw_prompt: str,
        model_name: Optional[str] = None,
        max_tokens: int = MODEL_CONFIG["default_max_tokens"],
        temperature: float = MODEL_CONFIG["default_temperature"],
        top_k: int = MODEL_CONFIG["default_top_k"]
    ) -> Tuple[str, float, int]:
        """Generate a response from raw prompt without additional formatting."""
        # Ensure model_name is set
        model_name = model_name or self.default_model
        print(f"Generating response with model: {model_name} (raw prompt)")

        # Validate parameters
        validate_parameters(temperature, max_tokens, top_k)

        # Use raw prompt directly - no formatting
        model, tokenizer = self.get_model(model_name)

        # Tokenize and generate with explicit attention_mask to avoid torch.isin MPS issues
        start_time = time.time()
        inputs = tokenizer(raw_prompt, return_tensors="pt", padding=True, truncation=True)

        # Move inputs to the same device as the model
        if hasattr(model, 'device'):
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        else:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Ensure we have attention_mask to prevent torch.isin comparison
        if 'attention_mask' not in inputs:
            inputs['attention_mask'] = torch.ones_like(inputs['input_ids'])

        # Conservative generation parameters for raw prompts
        gen_kwargs = {
            "temperature": min(temperature, 0.3),  # Very low temperature for raw prompts
            "do_sample": temperature > 0.0,
            "num_beams": 1,
            "top_k": min(top_k, 20),  # Very restricted vocabulary
            "top_p": 0.8,  # More focused sampling
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
            "use_cache": True,
            "return_dict_in_generate": False,
            # Aggressive anti-repetition for raw prompts
            "repetition_penalty": 1.5,  # Higher penalty for raw prompts
            "length_penalty": 0.8,  # Favor shorter responses
            "early_stopping": False,  # Let it stop naturally
            "max_new_tokens": min(max_tokens, 80)  # Very strict for raw prompts
        }

        # Generate with Causal LM (Llama models)
        # max_new_tokens is already in gen_kwargs to prevent conflicts
        outputs = model.generate(
            **inputs,
            **gen_kwargs
        )

        # Extract only the newly generated tokens (not the input prompt)
        input_length = inputs['input_ids'].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = tokenizer.decode(generated_tokens, skip_special_tokens=True)

        # Calculate metrics
        latency = time.time() - start_time
        tokens_used = len(outputs[0])

        print(f"🧠 Generated {len(generated_tokens)} new tokens, response length: {len(response)} chars")

        return response, latency, tokens_used

# Create a singleton instance
llm_manager = LLMManager()