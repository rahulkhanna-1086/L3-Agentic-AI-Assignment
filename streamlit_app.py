"""Streamlit interface for the Enterprise Knowledge Assistant."""

import asyncio
import logging

import streamlit as st

from enterprise_knowledge_assistant.config import Settings
from enterprise_knowledge_assistant.graph import EnterpriseKnowledgeGraph
from enterprise_knowledge_assistant.observability import configure_logging


st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="🏢",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 720px;
        margin-left: 3rem;
        margin-right: 2rem;
        padding-top: 2rem;
    }
    h1 {
        font-size: 2.3rem !important;
        line-height: 1.12 !important;
        white-space: normal !important;
        overflow-wrap: anywhere;
    }
    [data-testid="stMetric"] {
        background: #f7f9fc;
        border: 1px solid #e4e9f1;
        border-radius: 14px;
        padding: 0.9rem 1rem;
    }
    .app-kicker {
        color: #3563e9;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .app-subtitle {color: #5f6b7a; margin-top: -0.5rem;}
    .status-pill {
        display: inline-block;
        background: #eaf8ef;
        color: #18713b;
        border-radius: 999px;
        padding: 0.25rem 0.65rem;
        font-size: 0.8rem;
        font-weight: 650;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def create_assistant(demo_mode: bool) -> tuple[EnterpriseKnowledgeGraph, Settings]:
    """Create one graph instance for the selected UI mode."""

    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    logger_name = f"enterprise_knowledge_assistant.ui.{demo_mode}"
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        logger = configure_logging(settings.log_dir)
    return (
        EnterpriseKnowledgeGraph(
            settings=settings,
            logger=logger,
            demo_mode=demo_mode,
        ),
        settings,
    )


def render_result(result: dict) -> None:
    """Render answer evidence and evaluation details."""

    st.markdown(result["answer"])

    sources = result.get("sources", [])
    if sources:
        st.caption("Sources: " + " · ".join(sources))

    scores = result.get("scores", {})
    score_columns = st.columns(3)
    score_columns[0].metric(
        "Faithfulness",
        f"{scores.get('faithfulness', 0.0):.3f}",
    )
    score_columns[1].metric(
        "Answer relevancy",
        f"{scores.get('answer_relevancy', 0.0):.3f}",
    )
    score_columns[2].metric(
        "Retrieval attempts",
        str(result.get("attempt", 0)),
    )

    st.info(result.get("interpretation", "No interpretation available."))
    with st.expander("View execution trace"):
        for event in result.get("execution_log", []):
            st.code(event, language=None)


def reset_session() -> None:
    """Clear chat and initialized graph instances."""

    st.session_state.messages = []
    st.session_state.assistants = {}


st.markdown('<div class="app-kicker">Agentic AI · Internal Knowledge</div>', unsafe_allow_html=True)
st.title("Enterprise Knowledge Assistant")
st.markdown(
    '<p class="app-subtitle">Ask grounded questions across approved company policies, '
    "with sources and RAGAS quality scores for every answer.</p>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Assistant controls")
    mode_label = st.radio(
        "Execution mode",
        ("Live Ollama + RAGAS", "Offline demonstration"),
        help="Use Live mode for assignment evidence and genuine RAGAS scores.",
    )
    demo_mode = mode_label == "Offline demonstration"
    st.markdown(
        '<span class="status-pill">● Ready for questions</span>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("Knowledge source")
    st.write("3 approved HR policy documents")
    st.caption("Workflow")
    st.write("Retrieve → Respond → Evaluate")
    st.caption("Evaluation")
    st.write("Faithfulness · Answer relevancy")
    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        reset_session()
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "assistants" not in st.session_state:
    st.session_state.assistants = {}

if not st.session_state.messages:
    st.subheader("Try a policy question")
    suggestions = (
        "How many annual leave days are provided?",
        "When is a medical certificate required?",
        "What is the resignation notice period?",
    )
    for suggestion in suggestions:
        st.markdown(f"→ **{suggestion}**")
    st.divider()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            render_result(message["result"])
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about company policies"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    mode_key = "demo" if demo_mode else "live"
    if mode_key not in st.session_state.assistants:
        st.session_state.assistants[mode_key] = create_assistant(demo_mode)
    assistant, _settings = st.session_state.assistants[mode_key]

    with st.chat_message("assistant"):
        result = None
        with st.status(
            "Running Retriever → Response → Evaluator…",
            expanded=True,
        ) as status:
            st.write("Searching approved documents through MCP")
            try:
                result = asyncio.run(assistant.ask(prompt))
            except Exception as error:
                status.update(label="The request could not be completed", state="error")
                st.error(
                    "Please confirm Ollama is running and the configured models "
                    f"are available. Technical detail: {error}"
                )
            else:
                status.update(label="Answer evaluated", state="complete", expanded=False)
        if result is not None:
            render_result(result)
            st.session_state.messages.append(
                {"role": "assistant", "result": dict(result)}
            )
