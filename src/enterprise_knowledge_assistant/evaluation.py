"""RAGAS evaluation and score interpretation."""

import importlib.util
import sys
import types

from enterprise_knowledge_assistant.config import Settings


def _apply_ragas_vertexai_compatibility() -> None:
    """Bridge obsolete optional Vertex AI imports in RAGAS 0.4.3.

    RAGAS imports the removed LangChain Community Vertex AI modules even when
    the evaluator uses Ollama. Lightweight placeholder types keep that
    optional integration importable without changing the Ollama execution
    path. This guard can be removed after the upstream RAGAS fix is released.
    """

    module_names = (
        "langchain_community.chat_models.vertexai",
        "langchain_community.llms.vertexai",
    )
    missing_modules = [
        name for name in module_names if importlib.util.find_spec(name) is None
    ]
    if not missing_modules:
        return

    class _UnusedVertexAI:
        pass

    for module_name, class_name in zip(
        module_names, ("ChatVertexAI", "VertexAI"), strict=True
    ):
        if module_name not in missing_modules:
            continue
        compatibility_module = types.ModuleType(module_name)
        setattr(compatibility_module, class_name, _UnusedVertexAI)
        sys.modules[module_name] = compatibility_module

    from langchain_community import chat_models, llms

    if module_names[0] in missing_modules:
        chat_models.ChatVertexAI = _UnusedVertexAI
    if module_names[1] in missing_modules:
        llms.VertexAI = _UnusedVertexAI


def run_ragas_evaluation(
    question: str,
    answer: str,
    contexts: list[str],
    settings: Settings,
) -> dict[str, float]:
    """Evaluate one RAG answer using the two mandatory RAGAS metrics."""

    # Keep these imports local so the offline verification mode remains usable
    # while an assessor is installing the heavier RAGAS dependencies.
    from datasets import Dataset
    from langchain_ollama import ChatOllama, OllamaEmbeddings

    _apply_ragas_vertexai_compatibility()

    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, faithfulness

    dataset = Dataset.from_dict(
        {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        }
    )
    evaluator_llm = LangchainLLMWrapper(
        ChatOllama(model=settings.chat_model, temperature=0)
    )
    evaluator_embeddings = LangchainEmbeddingsWrapper(
        OllamaEmbeddings(model=settings.embedding_model)
    )
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        raise_exceptions=True,
    )
    row = result.to_pandas().iloc[0]
    return {
        "faithfulness": round(float(row["faithfulness"]), 3),
        "answer_relevancy": round(float(row["answer_relevancy"]), 3),
    }


def interpret_scores(scores: dict[str, float], threshold: float) -> str:
    """Convert metric values into a short, assessor-readable interpretation."""

    faithfulness_score = scores.get("faithfulness", 0.0)
    relevancy_score = scores.get("answer_relevancy", 0.0)

    if faithfulness_score >= threshold and relevancy_score >= threshold:
        return (
            "Good result: the answer is supported by the retrieved context "
            "and is relevant to the question."
        )
    if faithfulness_score < threshold and relevancy_score >= threshold:
        return (
            "The answer is relevant but may contain claims that are not fully "
            "supported by the retrieved context."
        )
    if faithfulness_score >= threshold and relevancy_score < threshold:
        return (
            "The answer is grounded in the context but does not fully address "
            "the question."
        )
    return (
        "Both grounding and relevancy are below the target. "
        "The graph will retry retrieval when another attempt is available."
    )
