"""Command-line entry point for the Enterprise Knowledge Assistant."""

import argparse
import asyncio
import json
from pathlib import Path

from enterprise_knowledge_assistant.config import Settings
from enterprise_knowledge_assistant.graph import EnterpriseKnowledgeGraph
from enterprise_knowledge_assistant.observability import configure_logging


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask a question about the enterprise knowledge base."
    )
    parser.add_argument(
        "--question",
        default="How many days of annual leave do employees receive?",
        help="Question sent to the knowledge assistant.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help=(
            "Run without Ollama using deterministic local components. "
            "This verifies the graph but does not replace the RAGAS evidence run."
        ),
    )
    return parser.parse_args()


async def run(question: str, demo_mode: bool) -> dict:
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logging(settings.log_dir)

    print("\n" + "=" * 70)
    print("ENTERPRISE KNOWLEDGE ASSISTANT")
    print("=" * 70)
    print(f"Mode: {'OFFLINE DEMO' if demo_mode else 'LIVE OLLAMA + RAGAS'}")
    print(f"Question: {question}")
    print("=" * 70 + "\n")

    assistant = EnterpriseKnowledgeGraph(
        settings=settings,
        logger=logger,
        demo_mode=demo_mode,
    )
    result = await assistant.ask(question)

    print("\n" + "=" * 70)
    print("FINAL ANSWER")
    print("=" * 70)
    print(result["answer"])
    print(f"\nSources: {', '.join(result['sources'])}")
    print("\nRAG EVALUATION")
    print("-" * 70)
    print(f"Backend: {result['evaluation_backend']}")
    for metric, score in result["scores"].items():
        print(f"{metric:20}: {score:.3f}")
    print(f"Interpretation: {result['interpretation']}")
    print(f"Retrieval attempts: {result['attempt']}")

    output_path = settings.output_dir / "latest_result.json"
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(f"\nSaved result: {output_path}")
    return result


def main() -> None:
    args = parse_arguments()
    asyncio.run(run(args.question, args.demo))


if __name__ == "__main__":
    main()

