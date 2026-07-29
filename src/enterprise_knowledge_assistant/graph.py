"""LangGraph workflow containing the three required agent nodes."""

import logging
from pathlib import Path
from typing import Literal

from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from enterprise_knowledge_assistant.config import Settings
from enterprise_knowledge_assistant.demo_components import (
    ExtractiveDemoModel,
    demo_scores,
)
from enterprise_knowledge_assistant.evaluation import (
    interpret_scores,
    run_ragas_evaluation,
)
from enterprise_knowledge_assistant.mcp_client import KnowledgeMCPClient
from enterprise_knowledge_assistant.rag import RAGService
from enterprise_knowledge_assistant.state import AssistantState


class EnterpriseKnowledgeGraph:
    """Orchestrate retrieval, response generation, and RAGAS evaluation."""

    def __init__(
        self,
        settings: Settings,
        logger: logging.Logger,
        demo_mode: bool = False,
    ):
        self.settings = settings
        self.logger = logger
        self.demo_mode = demo_mode
        self.rag = RAGService(settings, demo_mode=demo_mode)
        self.model = (
            ExtractiveDemoModel()
            if demo_mode
            else ChatOllama(model=settings.chat_model, temperature=0)
        )
        server_path = Path(__file__).with_name("mcp_server.py")
        self.mcp_client = KnowledgeMCPClient(server_path)
        self._index_ready = False
        self.graph = self._build_graph()

    def _trace(self, node: str, message: str) -> str:
        line = f"{node} | {message}"
        self.logger.info(line)
        return line

    async def retriever_agent(self, state: AssistantState) -> dict:
        """Load knowledge through MCP, build Chroma, and retrieve context."""

        attempt = state.get("attempt", 0) + 1
        trace = self._trace(
            "RETRIEVER AGENT - INPUT",
            f"question={state['question']!r}, attempt={attempt}",
        )

        if not self._index_ready:
            documents = await self.mcp_client.load_documents()
            chunk_count = self.rag.build_index(documents)
            self._index_ready = True
            self._trace(
                "MCP FILESYSTEM",
                f"loaded {len(documents)} files; created {chunk_count} chunks",
            )

        k = self.settings.retrieval_k + (attempt - 1) * 2
        retrieved_documents = self.rag.retrieve(state["question"], k=k)
        contexts = [document.page_content for document in retrieved_documents]
        sources = sorted(
            {
                str(document.metadata.get("source", "unknown"))
                for document in retrieved_documents
            }
        )
        output_trace = self._trace(
            "RETRIEVER AGENT - OUTPUT",
            f"retrieved={len(contexts)}, sources={sources}",
        )
        return {
            "contexts": contexts,
            "sources": sources,
            "attempt": attempt,
            "execution_log": state.get("execution_log", [])
            + [trace, output_trace],
        }

    def response_agent(self, state: AssistantState) -> dict:
        """Generate a grounded answer using only retrieved context."""

        trace = self._trace(
            "RESPONSE AGENT - INPUT",
            f"contexts={len(state['contexts'])}",
        )
        context = "\n\n".join(state["contexts"])
        prompt = f"""
You are a helpful Enterprise Knowledge Assistant.

Answer ONLY using the provided context.
If the answer is not present in the context, reply:
"I could not find that information in the knowledge base."
Give a concise answer and do not invent facts.

Context:
{context}

Question:
{state["question"]}
""".strip()
        response = self.model.invoke(prompt)
        answer = str(response.content).strip()
        output_trace = self._trace(
            "RESPONSE AGENT - OUTPUT",
            f"answer={answer!r}",
        )
        return {
            "answer": answer,
            "execution_log": state["execution_log"] + [trace, output_trace],
        }

    def evaluator_agent(self, state: AssistantState) -> dict:
        """Evaluate the response and provide a short score interpretation."""

        trace = self._trace(
            "EVALUATOR AGENT - INPUT",
            f"answer_length={len(state['answer'])}",
        )
        if self.demo_mode:
            scores = demo_scores(
                state["question"],
                state["answer"],
                state["contexts"],
            )
            backend = "offline-demo-proxy"
        else:
            scores = run_ragas_evaluation(
                state["question"],
                state["answer"],
                state["contexts"],
                self.settings,
            )
            backend = "ragas"

        interpretation = interpret_scores(
            scores,
            self.settings.score_threshold,
        )
        output_trace = self._trace(
            "EVALUATOR AGENT - OUTPUT",
            f"backend={backend}, scores={scores}",
        )
        return {
            "scores": scores,
            "interpretation": interpretation,
            "evaluation_backend": backend,
            "execution_log": state["execution_log"] + [trace, output_trace],
        }

    def route_after_evaluation(
        self,
        state: AssistantState,
    ) -> Literal["retry", "end"]:
        """Retry retrieval once when either mandatory score is too low."""

        lowest_score = min(state["scores"].values())
        if (
            lowest_score < self.settings.score_threshold
            and state["attempt"] <= self.settings.max_retries
        ):
            self._trace(
                "CONDITIONAL EDGE",
                f"score={lowest_score:.3f}; route=retry",
            )
            return "retry"

        self._trace(
            "CONDITIONAL EDGE",
            f"score={lowest_score:.3f}; route=end",
        )
        return "end"

    def _build_graph(self):
        """Compile Retrieve -> Respond -> Evaluate with a bonus retry edge."""

        builder = StateGraph(AssistantState)

        builder.add_node("retriever_agent", self.retriever_agent)
        builder.add_node("response_agent", self.response_agent)
        builder.add_node("evaluator_agent", self.evaluator_agent)

        builder.add_edge(START, "retriever_agent")
        builder.add_edge("retriever_agent", "response_agent")
        builder.add_edge("response_agent", "evaluator_agent")
        builder.add_conditional_edges(
            "evaluator_agent",
            self.route_after_evaluation,
            {
                "retry": "retriever_agent",
                "end": END,
            },
        )
        return builder.compile()

    async def ask(self, question: str) -> AssistantState:
        """Run the complete graph for one question."""

        initial_state: AssistantState = {
            "question": question,
            "contexts": [],
            "sources": [],
            "answer": "",
            "scores": {},
            "interpretation": "",
            "attempt": 0,
            "execution_log": [],
            "evaluation_backend": "",
        }
        return await self.graph.ainvoke(initial_state)

