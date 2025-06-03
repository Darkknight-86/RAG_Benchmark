import torch
from transformers import AutoTokenizer, AutoModel

class SpecterEmbedder:
    def __init__(self, model_name="allenai/specter2_base"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def embed(self, texts):
        self.model.eval()
        embeddings = []

        with torch.no_grad():
            for text in texts:
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                outputs = self.model(**inputs)
                cls_embedding = outputs.last_hidden_state[:, 0, :]  # CLS token
                embeddings.append(cls_embedding.squeeze().cpu().numpy())

        return embeddings