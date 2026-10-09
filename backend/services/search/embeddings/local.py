from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from services.search.embeddings.base import BaseEmbeddingProvider


class LocalEmbeddingProvider(BaseEmbeddingProvider):

    def __init__(self):
        model_dir = (
            Path(__file__).resolve().parent
            / "models"
            / "all-MiniLM-L6-v2"
        )

        self.model_path = model_dir /"onnx" / "model_q4.onnx"
        self.tokenizer_path = model_dir / "tokenizer.json"

        self.tokenizer = Tokenizer.from_file(
            str(self.tokenizer_path)
        )

        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )

    def get_embedding(self, text: str) -> list:
        if not text or not text.strip():
            raise ValueError("Le texte ne peut pas être vide.")

        encoded = self.tokenizer.encode(text.strip())

        input_ids = np.array(
            [encoded.ids],
            dtype=np.int64,
        )

        attention_mask = np.array(
            [encoded.attention_mask],
            dtype=np.int64,
        )

        token_type_ids = np.array(
            [encoded.type_ids],
            dtype=np.int64,
        )

        outputs = self.session.run(
            ["last_hidden_state"],
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )

        last_hidden_state = outputs[0]

        # Mean pooling en ignorant les tokens de padding.
        mask = attention_mask[..., np.newaxis]

        summed = np.sum(
            last_hidden_state * mask,
            axis=1,
        )

        count = np.clip(
            mask.sum(axis=1),
            a_min=1e-9,
            a_max=None,
        )

        embedding = summed / count

        # L2 normalization
        embedding = embedding / np.linalg.norm(
            embedding,
            axis=1,
            keepdims=True,
        )

        return embedding[0].tolist()

    @property
    def dimensions(self) -> int:
        return 384