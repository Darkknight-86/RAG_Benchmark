from typing import Dict, Optional, Tuple, Union
import time
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from dotenv import load_dotenv
import os
from .config import MODEL_CONFIG, validate_parameters
from .prompt_manager import prompt_manager

load_dotenv()

class LLMManager:
    """Manages different LLM models from Hugging Face."""

    def __init__(self):
        self.models: Dict[str, Tuple[Union[AutoModelForCausalLM, AutoModelForSeq2SeqLM], AutoTokenizer]] = {}
        self.default_model = MODEL_CONFIG["default_model"]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

    def load_model(self, model_name: str) -> None:
        """Load a model from Hugging Face."""
        if model_name in self.models:
            return

        if model_name not in MODEL_CONFIG["supported_models"]:
            raise ValueError(f"Model {model_name} is not in supported models list")

        print(f"Loading model: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # For CPU, we don't use device_map
        device_map_arg = "auto" if self.device == "cuda" else None

        # Try loading as causal LM first
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,  # Always use float32 for CPU
                device_map=device_map_arg,
                low_cpu_mem_usage=True
            )
        except ValueError:
            # If that fails, try loading as seq2seq model (Flan-T5 etc.)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,  # Always use float32 for CPU
                device_map=device_map_arg,
                low_cpu_mem_usage=True
            )

        # Move model to device if not using device_map
        if device_map_arg is None:
            model = model.to(self.device)

        self.models[model_name] = (model, tokenizer)
        print(f"Model loaded successfully on {self.device}")

    def get_model(self, model_name: Optional[str] = None) -> Tuple[Union[AutoModelForCausalLM, AutoModelForSeq2SeqLM], AutoTokenizer]:
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

        # Handle different model types
        if isinstance(model, AutoModelForCausalLM):
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                **gen_kwargs
            )
        else:  # Seq2Seq model
            outputs = model.generate(
                **inputs,
                max_length=max_tokens,
                **gen_kwargs
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Calculate metrics
        latency = time.time() - start_time
        tokens_used = len(outputs[0])

        return response, latency, tokens_used

# Create a singleton instance
llm_manager = LLMManager()