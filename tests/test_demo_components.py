from enterprise_knowledge_assistant.demo_components import (
    HashEmbeddings,
    demo_scores,
)
from enterprise_knowledge_assistant.main import is_exit_command


def test_hash_embeddings_are_deterministic():
    embeddings = HashEmbeddings(dimensions=32)
    first = embeddings.embed_query("annual leave policy")
    second = embeddings.embed_query("annual leave policy")

    assert first == second
    assert len(first) == 32


def test_demo_scores_are_bounded():
    scores = demo_scores(
        question="How many annual leave days are provided?",
        answer="Employees receive 24 annual leave days.",
        contexts=["Employees receive 24 annual leave days each year."],
    )

    assert set(scores) == {"faithfulness", "answer_relevancy"}
    assert all(0.0 <= score <= 1.0 for score in scores.values())


def test_interactive_exit_commands():
    assert is_exit_command("quit")
    assert is_exit_command(" EXIT ")
    assert not is_exit_command("What is the exit procedure?")
