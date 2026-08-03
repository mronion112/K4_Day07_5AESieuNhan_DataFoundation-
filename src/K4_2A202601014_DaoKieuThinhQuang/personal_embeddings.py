from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter


class VietnameseLexicalEmbedder:
    """Dependency-free lexical embedding for Vietnamese policy retrieval.

    This is not a neural semantic model. It is a transparent hashing-vectorizer
    baseline that preserves Vietnamese word and bigram overlap, making it much
    more suitable for retrieval experiments than the repository's random mock.
    """

    TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
    STOPWORDS = {
        "a",
        "bi",
        "cac",
        "cho",
        "co",
        "cua",
        "da",
        "de",
        "do",
        "duoc",
        "gi",
        "hang",
        "hoa",
        "khi",
        "la",
        "mot",
        "nao",
        "nay",
        "nhung",
        "o",
        "nguoi",
        "quy",
        "dinh",
        "chinh",
        "sach",
        "san",
        "pham",
        "shopee",
        "the",
        "thi",
        "tren",
        "trong",
        "tu",
        "va",
        "voi",
    }

    INTENT_EXPANSIONS = {
        "hau qua": ("che tai", "xu ly vi pham"),
        "hinh thuc tra hang": ("don vi van chuyen", "buu cuc", "tu sap xep", "mien phi"),
        "khong duoc phep": (
            "nghiem cam",
            "noi dung cam",
            "cam dang",
        ),
        "truong hop nao": ("dang ky", "giao dich", "tuong tac", "truy cap"),
        "khi nao": ("dang ky", "giao dich", "tuong tac", "truy cap"),
    }

    def __init__(self, dim: int = 4096) -> None:
        if dim <= 0:
            raise ValueError("dim must be greater than zero")
        self.dim = dim
        self._backend_name = "vietnamese lexical hashing (word + bigram)"

    @staticmethod
    def _normalize(text: str) -> str:
        decomposed = unicodedata.normalize("NFD", text.casefold())
        without_marks = "".join(
            char for char in decomposed if unicodedata.category(char) != "Mn"
        )
        return without_marks.replace("đ", "d")

    @staticmethod
    def _index(term: str, dim: int) -> int:
        digest = hashlib.blake2b(term.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % dim

    def __call__(self, text: str) -> list[float]:
        normalized_text = self._normalize(text)
        tokens = self.TOKEN_PATTERN.findall(normalized_text)
        content_tokens = [token for token in tokens if token not in self.STOPWORDS]

        expanded_tokens: list[str] = []
        # Retrieval queries are short; only expand their intent. Expanding the
        # repeated section heading inside every document chunk would remove the
        # ranking signal from the body content.
        if len(tokens) <= 30:
            for intent, expansions in self.INTENT_EXPANSIONS.items():
                if intent in normalized_text:
                    for expansion in expansions:
                        expanded_tokens.extend(expansion.split())
        features: list[tuple[str, float]] = [
            (f"w:{token}", 1.0) for token in content_tokens
        ]
        features.extend(
            (f"b:{left}_{right}", 1.6)
            for left, right in zip(content_tokens, content_tokens[1:])
        )
        features.extend((f"w:{token}", 4.0) for token in expanded_tokens)
        features.extend(
            (f"b:{left}_{right}", 5.0)
            for left, right in zip(expanded_tokens, expanded_tokens[1:])
        )

        counts = Counter(term for term, _ in features)
        weights = {term: weight for term, weight in features}
        vector = [0.0] * self.dim
        for term, count in counts.items():
            vector[self._index(term, self.dim)] += weights[term] * (1.0 + math.log(count))

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
