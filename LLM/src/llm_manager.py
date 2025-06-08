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
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Get Hugging Face token for gated models
        self.hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if self.hf_token:
            print("🔑 Using Hugging Face authentication token")
        else:
            print("⚠️ No Hugging Face token found - some models may not be accessible")
        print(f"Using device: {self.device}")

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

        # Set padding token for models that don't have one
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # For CPU, we don't use device_map
        device_map_arg = "auto" if self.device == "cuda" else None

        # Common model loading arguments
        model_kwargs = {
            'torch_dtype': torch.float32,  # Always use float32 for CPU
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

        # Tokenize and generate
        start_time = time.time()
        inputs = tokenizer(formatted_prompt, return_tensors="pt")

        # Move inputs to the same device as the model
        if hasattr(model, 'device'):
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        else:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Get model requirements
        model_reqs = prompt_manager.get_model_requirements(model_name)

        # Common generation parameters
        gen_kwargs = {
            "temperature": temperature,
            "do_sample": temperature > 0.0,  # Only sample if temperature > 0
            "num_beams": 5,  # Use beam search for better quality
            "early_stopping": True,
            "pad_token_id": tokenizer.eos_token_id,
            "no_repeat_ngram_size": 3,  # Prevent repetition
            "top_k": top_k
        }

        # Generate with Causal LM (Llama models)
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
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

# Create a singleton instance
llm_manager = LLMManager()