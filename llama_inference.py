import os
from llama_cpp import Llama

# Optimal settings for 8GB RAM:
# - Q4_K_M model (already set)
# - n_ctx=512 (reduces memory usage)
# - n_threads=4 (adjust to match your CPU cores)

CACHE_DIR = "models/mistral-7b-instruct-v0.2-gguf/models--TheBloke--Mistral-7B-Instruct-v0.2-GGUF/snapshots/3a6fbf4a41a1d52e415a4958cde6856d34b2db93"
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"

def load_model():
    model_path = os.path.join(CACHE_DIR, MODEL_FILENAME)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    llm = Llama(model_path=model_path, n_threads=6, n_ctx=1536)  # Adjust n_threads if your CPU has more/less cores
    return llm

def run_inference(prompt, max_tokens=256):
    llm = load_model()
    output = llm(prompt, max_tokens=max_tokens, stop=["</s>"])
    print("Response:\n", output["choices"][0]["text"].strip())

if __name__ == "__main__":
    while True:
        prompt = input("Enter your prompt (or 'exit' to quit): ")
        if prompt.lower() == "exit":
            break
        run_inference(prompt) 