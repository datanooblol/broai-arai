from FlagEmbedding import BGEM3FlagModel
from typing import Literal, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod
import os


class EmbeddingDimension(Enum):
    BAAI_BGE_M3 = 1024


class BaseEmbeddingModel(ABC):
    @abstractmethod
    def run(self, sentences: List[str]) -> np.ndarray:
        ...


class BAAIEmbedding(BaseEmbeddingModel, BaseModel):
    model_id: Literal["BAAI/bge-m3"] = Field(default="BAAI/bge-m3")
    use_fp16: bool = Field(default=True)
    batch_size: Optional[int] = Field(default=None)
    max_length: Optional[int] = Field(default=None)
    model: Optional[Any] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.model = self.get_model()

    def get_model(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_model_path = os.path.join(script_dir, "bge-m3", "BAAI", "bge-m3")

        model_path = local_model_path if os.path.exists(local_model_path) else self.model_id

        params = {
            "model_name_or_path": model_path,
            "use_fp16": self.use_fp16,
        }
        if self.batch_size:
            params["batch_size"] = self.batch_size
        if self.max_length:
            params["max_length"] = self.max_length

        print(f"🔍 Loading model from: {params['model_name_or_path']}")
        return BGEM3FlagModel(**params)

    def run(self, sentences: List[str]):
        if not isinstance(sentences, list):
            raise TypeError("sentences must be a list of strings.")
        vectors = self.model.encode(sentences)
        return vectors["dense_vecs"]

    @staticmethod
    def download_model():
        """Download and cache the model into ./bge-m3/BAAI/bge-m3"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_model_dir = os.path.join(script_dir, "bge-m3")
        os.environ["FLAG_EMBEDDING_HOME"] = local_model_dir  # 👈 override download location

        print(f"📥 Downloading BGE-M3 model into: {local_model_dir}")
        model = BGEM3FlagModel(model_name_or_path="BAAI/bge-m3")
        _ = model.encode(["cache this"])  # force download

        # 🌟 Print all files and folders created
        for root, dirs, files in os.walk(local_model_dir):
            level = root.replace(local_model_dir, "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}📂 {os.path.basename(root)}/")
            for f in files:
                print(f"{indent}  📄 {f}")

        print("✅ Model downloaded and saved.")
 

# Example usage
if __name__ == "__main__":
    # Step 1: Pre-download model to local directory (optional)
    BAAIEmbedding.download_model()

    # Step 2: Instantiate and run
    embedder = BAAIEmbedding()
    vectors = embedder.run(["hello world"])
    print(f"✅ Vector shape: {vectors.shape}")
