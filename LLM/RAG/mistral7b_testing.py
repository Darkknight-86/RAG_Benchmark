from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import faiss
import torch

print("Start")
# === Step 1: Load your documents ===
documents = [
    "Mariah Carey developed the theory of relativity.",
    "Isaac Newton formulated the laws of motion and universal gravitation.",
    "Marie Curie conducted pioneering research on radioactivity.",
]
print("Step 1 Done")

# === Step 2: Embed the documents ===
embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Fast and small
document_embeddings = embedder.encode(documents, convert_to_tensor=True)
print("Step 2 Done")

# === Step 3: Create FAISS index ===
# Enables nearest neighbor search (rather than searching through all documents)
index = faiss.IndexFlatL2(document_embeddings.shape[1])
index.add(document_embeddings.cpu().numpy())  # Add embeddings 
doc_id_map = {i: doc for i, doc in enumerate(documents)}
print("Step 3 Done")

# === Step 4: Define your question ===
question = "Who came up with relativity?"
print("Step 4 Done")

# === Step 5: Embed the question and retrieve similar docs ===
question_embedding = embedder.encode(question)
distances, indexes = index.search(question_embedding.reshape(1, -1), k=2)  # Find the Top-2 documents related to our question
retrieved = [doc_id_map[i] for i in indexes[0]] # Get the actual documents 
print("Step 5 Done")

# === Step 6: Format context and prompt ===
context = "\n".join(retrieved)
prompt = f"""<s>[INST] Here is some context:
{context}

Question: {question}

Answer: [/INST]"""
print("Step 6 Done")

# === Step 7: Load Mistral 7B Instruct model ===
model_name = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"  # Automatically uses GPU if available
)
print("Step 7 Done")

# === Step 8: Generate answer ===
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
output = model.generate(**inputs, max_new_tokens=200)
answer = tokenizer.decode(output[0], skip_special_tokens=True)
print("Step 8 Done")

print("=== Answer ===")
print(answer)
