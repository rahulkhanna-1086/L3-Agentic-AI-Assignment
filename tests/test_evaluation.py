from enterprise_knowledge_assistant.evaluation import (
    _apply_ragas_vertexai_compatibility,
    interpret_scores,
)


def test_interpretation_reports_good_result():
    interpretation = interpret_scores(
        {"faithfulness": 0.9, "answer_relevancy": 0.8},
        threshold=0.7,
    )

    assert interpretation.startswith("Good result")


def test_interpretation_reports_low_grounding():
    interpretation = interpret_scores(
        {"faithfulness": 0.4, "answer_relevancy": 0.9},
        threshold=0.7,
    )

    assert "not fully supported" in interpretation


def test_ragas_compatibility_guard_can_run_more_than_once():
    _apply_ragas_vertexai_compatibility()
    _apply_ragas_vertexai_compatibility()
