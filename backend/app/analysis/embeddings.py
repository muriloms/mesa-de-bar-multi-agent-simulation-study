"""Camada de embeddings plugável + cache em disco.

Backends (env MDB_EMBED_BACKEND):
  - google (default): API text-embedding-004 (multilíngue, determinístico).
    Chave em MDB_EMBED_API_KEY ou GOOGLE_API_KEY.
  - local: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2),
    offline e reprodutível (requer instalar sentence-transformers).
  - hash: pseudo-embedding determinístico (sem rede) — só p/ testes/dev,
    NÃO use para análise real (não é semântico).

Cache append-only em data/analysis/embeddings_cache.jsonl, chaveado por
sha256(backend:model::texto). Reexecuções não recomputam.
"""
import hashlib
import json
import math
import os
import struct
from typing import Dict, List, Optional

from core import config


GOOGLE_MODEL = "models/text-embedding-004"
LOCAL_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
HASH_DIM = 64


def _backend() -> str:
    return os.getenv("MDB_EMBED_BACKEND", "google").lower()


def _cache_path():
    return config.DATA_DIR / "analysis" / "embeddings_cache.jsonl"


def _cache_key(tag: str, text: str) -> str:
    return hashlib.sha256((tag + "::" + text).encode("utf-8")).hexdigest()


class EmbeddingProvider:
    """Carrega cache, despacha pro backend e persiste novos vetores."""

    def __init__(self, backend: Optional[str] = None):
        self.backend = (backend or _backend()).lower()
        self.tag = {"google": f"google:{GOOGLE_MODEL}",
                    "local": f"local:{LOCAL_MODEL}",
                    "hash": "hash:v1"}.get(self.backend, self.backend)
        self._cache: Dict[str, List[float]] = {}
        self._local_model = None
        self._google_ready = False
        self._load_cache()

    # ---- cache ----
    def _load_cache(self):
        path = _cache_path()
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                self._cache[rec["key"]] = rec["vec"]
            except (json.JSONDecodeError, KeyError):
                continue

    def _persist(self, key: str, vec: List[float]):
        path = _cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"key": key, "vec": vec}) + "\n")

    # ---- backends ----
    def _embed_google(self, text: str) -> List[float]:
        import google.generativeai as genai
        if not self._google_ready:
            key = os.getenv("MDB_EMBED_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if key:
                genai.configure(api_key=key)
            self._google_ready = True
        resp = genai.embed_content(model=GOOGLE_MODEL, content=text,
                                   task_type="semantic_similarity")
        return list(resp["embedding"])

    def _embed_local(self, text: str) -> List[float]:
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(LOCAL_MODEL)
        return [float(x) for x in self._local_model.encode(text)]

    def _embed_hash(self, text: str) -> List[float]:
        # Pseudo-embedding determinístico: deriva HASH_DIM floats do sha256.
        out: List[float] = []
        i = 0
        while len(out) < HASH_DIM:
            h = hashlib.sha256(f"{i}:{text}".encode("utf-8")).digest()
            for j in range(0, len(h), 4):
                if len(out) >= HASH_DIM:
                    break
                val = struct.unpack("<I", h[j:j + 4])[0]
                out.append((val / 2**32) * 2 - 1)  # [-1, 1]
            i += 1
        norm = math.sqrt(sum(x * x for x in out)) or 1.0
        return [x / norm for x in out]

    def _embed_one(self, text: str) -> List[float]:
        if self.backend == "google":
            return self._embed_google(text)
        if self.backend == "local":
            return self._embed_local(text)
        return self._embed_hash(text)

    # ---- API pública ----
    def embed(self, text: str) -> List[float]:
        text = (text or "").strip()
        if not text:
            return [0.0] * HASH_DIM
        key = _cache_key(self.tag, text)
        if key in self._cache:
            return self._cache[key]
        vec = self._embed_one(text)
        self._cache[key] = vec
        self._persist(key, vec)
        return vec

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]
