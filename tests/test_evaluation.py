from enterprise_knowledge_assistant.evaluation import interpret_scores


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

