# scripts/download_embedding_model.py

from pathlib import Path
from huggingface_hub import snapshot_download

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = (
    BASE_DIR
    / "services"
    / "search"
    / "embeddings"
    / "models"
    / "all-MiniLM-L6-v2"
)

def main():
    path = snapshot_download(
        repo_id="onnx-community/all-MiniLM-L6-v2-ONNX",
        allow_patterns=[
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.txt",
            "onnx/model_q4.onnx",
            "onnx/model_q4.onnx_data",
        ],
        local_dir=str(MODEL_DIR),
    )

    print(f"Modèle téléchargé dans : {path}")

if __name__ == "__main__":
    main()