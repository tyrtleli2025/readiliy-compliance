import re
from collections import Counter

TOP_K_DOCS = 15


def _tokenize(text: str) -> Counter:
    return Counter(re.findall(r"[a-z]{3,}", text.lower()))


class PolicyIndex:
    def __init__(self, library: dict[str, str]) -> None:
        self._names = list(library.keys())
        self._texts = list(library.values())
        self._term_counts = [_tokenize(t) for t in self._texts]

    def __len__(self) -> int:
        return len(self._names)

    def retrieve(self, query: str, top_k: int = TOP_K_DOCS) -> str:
        query_terms = _tokenize(query)
        scores = [
            sum(min(query_terms[t], doc[t]) for t in query_terms if t in doc)
            for doc in self._term_counts
        ]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        parts = [
            f"--- Document: {self._names[i]} ---\n{self._texts[i]}"
            for i in ranked[:top_k]
        ]
        return "\n\n".join(parts)
