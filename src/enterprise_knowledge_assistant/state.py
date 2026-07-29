"""Shared LangGraph state."""

from typing import TypedDict


class AssistantState(TypedDict):
    """Data passed between the Retriever, Response, and Evaluator agents."""

    question: str
    contexts: list[str]
    sources: list[str]
    answer: str
    scores: dict[str, float]
    interpretation: str
    attempt: int
    execution_log: list[str]
    evaluation_backend: str

