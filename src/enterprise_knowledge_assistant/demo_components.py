"""Deterministic local components used for testing and assessor-friendly demos."""

from collections import Counter
import hashlib
import math
import re

from langchain_core.embeddings import Embeddings


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Return normalized word tokens."""

    return TOKEN_PATTERN.findall(text.lower())


class HashEmbeddings(Embeddings):
    """Small deterministic embedding model with no download or API key."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token, count in Counter(tokenize(text)).items():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign * count

        magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / magnitude for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class ExtractiveDemoModel:
    """Generate a deterministic answer from the most relevant context."""

    def invoke(self, prompt: str) -> object:
        question_marker = "Question:\n"
        context_marker = "Context:\n"
        question = prompt.split(question_marker, 1)[-1].strip()
        context_block = prompt.split(context_marker, 1)[-1].split(
            question_marker,
            1,
        )[0]

        question_tokens = set(tokenize(question))
        sentences = re.split(r"(?<=[.!?])\s+", context_block)
        ranked = sorted(
            sentences,
            key=lambda sentence: len(question_tokens & set(tokenize(sentence))),
            reverse=True,
        )
        selected = [sentence.strip() for sentence in ranked[:1] if sentence.strip()]
        content = " ".join(selected)

        if not content:
            content = "I could not find that information in the knowledge base."

        return type("DemoResponse", (), {"content": content})()


def demo_scores(
    question: str,
    answer: str,
    contexts: list[str],
) -> dict[str, float]:
    """Calculate transparent proxy scores for offline graph verification."""

    answer_tokens = set(tokenize(answer))
    question_tokens = set(tokenize(question))
    context_tokens = set(tokenize(" ".join(contexts)))

    faithfulness = (
        len(answer_tokens & context_tokens) / len(answer_tokens)
        if answer_tokens
        else 0.0
    )
    answer_relevancy = (
        len(answer_tokens & question_tokens) / len(question_tokens)
        if question_tokens
        else 0.0
    )

    return {
        "faithfulness": round(min(faithfulness, 1.0), 3),
        "answer_relevancy": round(min(answer_relevancy * 2.0, 1.0), 3),
    }
