# Enterprise Knowledge Assistant

An AI-powered internal policy assistant built with LangGraph, retrieval-
augmented generation (RAG), RAGAS evaluation, and an actively used filesystem
MCP server.

## 1. Architecture overview

```text
User question
     |
     v
Retriever Agent --MCP--> Filesystem knowledge tools
     |                    - list_knowledge_files
     |                    - read_knowledge_file
     |                              |
     +--> chunking --> embeddings --> Chroma --> relevant context
     |
     v
Response Agent --> grounded answer using Ollama
     |
     v
Evaluator Agent --> RAGAS Faithfulness + Answer Relevancy
     |
     +-- score below 0.70 and retry available --> Retriever Agent
     |
     v
    End
```

The normal path is linear as required:

`Retrieve -> Respond -> Evaluate -> End`

A conditional edge provides the bonus retry path when either mandatory RAGAS
score is below the configured threshold.

## 2. Main technologies

| Requirement | Implementation |
|---|---|
| LangGraph | Three explicit nodes using `StateGraph` |
| Document source | Markdown HR policies under `knowledge_base/` |
| MCP | Local FastMCP stdio server used by the Retriever Agent |
| Chunking | `RecursiveCharacterTextSplitter`, 500 characters, 100 overlap |
| Embeddings | Ollama `nomic-embed-text` |
| Vector database | Persistent local Chroma collection |
| Generation model | Ollama `gpt-oss:120b-cloud` by default |
| RAGAS | Faithfulness and Answer Relevancy |
| Observability | Timestamped console and file logs for every node |

## 3. Project structure

```text
enterprise_knowledge_assistant/
|-- knowledge_base/              # Approved enterprise source documents
|-- screenshots/                 # Execution evidence goes here
|-- src/enterprise_knowledge_assistant/
|   |-- config.py                # Safe environment-based settings
|   |-- graph.py                 # LangGraph nodes and edges
|   |-- rag.py                   # Chunking, embeddings, Chroma retrieval
|   |-- evaluation.py            # RAGAS evaluation
|   |-- mcp_server.py            # Filesystem MCP tools
|   |-- mcp_client.py            # MCP calls made by Retriever Agent
|   |-- observability.py         # Console and file tracing
|   |-- demo_components.py       # Offline verification components
|   `-- main.py                  # Command-line application
|-- tests/
|-- pyproject.toml
|-- requirements.txt
`-- README.md
```

## 4. Prerequisites

- Python 3.12, 3.13, or 3.14
- Ollama installed and running
- Access to the configured Ollama chat model
- No API key is required for the default local MCP and Chroma components

The trainer's examples use Ollama and `uv`; the commands below follow the same
style.

## 5. Setup

From this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Pull the local embedding model:

```powershell
ollama pull nomic-embed-text
```

The default chat model is `gpt-oss:120b-cloud`. To use another Ollama model:

```powershell
$env:OLLAMA_CHAT_MODEL = "your-model-name"
```

Optional settings:

```powershell
$env:OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
$env:RAG_CHUNK_SIZE = "500"
$env:RAG_CHUNK_OVERLAP = "100"
$env:RAG_RETRIEVAL_K = "4"
$env:RAG_SCORE_THRESHOLD = "0.70"
$env:RAG_MAX_RETRIES = "1"
```

No `.env` file is needed. Never add credentials or secrets to the submission.

## 6. Run the application

Set the source path for the current PowerShell session:

```powershell
$env:PYTHONPATH = "src"
```

Run the live Ollama and RAGAS workflow:

```powershell
python -m enterprise_knowledge_assistant.main `
  --question "How many days of annual leave do employees receive?"
```

Expected output includes:

```text
RETRIEVER AGENT - INPUT
MCP FILESYSTEM | loaded 3 files
RETRIEVER AGENT - OUTPUT
RESPONSE AGENT - INPUT
RESPONSE AGENT - OUTPUT
EVALUATOR AGENT - INPUT
EVALUATOR AGENT - OUTPUT | backend=ragas

FINAL ANSWER
Permanent employees receive 24 working days of paid annual leave...

RAG EVALUATION
Backend: ragas
faithfulness        : <score>
answer_relevancy    : <score>
```

Results are saved to `output/latest_result.json`. Full node-by-node logs are
saved to `logs/execution_YYYYMMDD_HHMMSS.log`.

## 7. Offline verification mode

If Ollama is temporarily unavailable, the complete LangGraph, MCP, chunking,
embedding, Chroma, retrieval, logging, retry, and output path can be verified:

```powershell
python -m enterprise_knowledge_assistant.main --demo `
  --question "Can employees work from home?"
```

This mode is clearly labeled `offline-demo-proxy`. Its transparent lexical
scores are not RAGAS and must not be submitted as RAGAS execution evidence.

## 8. Run tests

```powershell
pytest -q
```

The tests cover deterministic embeddings, evaluation interpretation, and MCP
filesystem path restrictions.

## 9. RAG design

The Retriever Agent calls the MCP server to list and read all approved
knowledge files. It converts each file into a LangChain `Document`, splits the
documents with a recursive character splitter, creates embeddings, and stores
them in a persistent Chroma collection. For each question, Chroma returns the
four most relevant chunks and their source filenames.

The chunk size of 500 characters preserves short policy sections, while the
100-character overlap reduces the chance that a policy condition is separated
from its outcome. On a low evaluation score, the bonus retry retrieves two
additional chunks.

## 10. LangGraph design

### Retriever Agent

- Actively invokes the filesystem MCP server.
- Loads and chunks approved knowledge documents.
- Generates embeddings and builds the Chroma vector database.
- Retrieves relevant context and records source filenames.

### Response Agent

- Receives the question and retrieved context.
- Instructs the model to answer only from that context.
- Uses a fixed fallback sentence when the information is absent.

### Evaluator Agent

- Creates a one-row RAGAS evaluation dataset.
- Calculates mandatory Faithfulness and Answer Relevancy.
- Displays both scores and a plain-language interpretation.
- Routes to retrieval once more when a score is below 0.70.

## 11. MCP integration

`mcp_server.py` exposes two tools:

- `list_knowledge_files`: lists approved Markdown and text documents.
- `read_knowledge_file`: reads one approved document.

The Retriever Agent launches the server using the stdio transport and invokes
both tools. The server rejects parent-directory traversal and unsupported file
types, so it cannot read arbitrary files outside the knowledge base.

## 12. RAGAS evaluation

The live evaluator uses:

- **Faithfulness**: checks whether answer claims are supported by retrieved
  context.
- **Answer Relevancy**: checks whether the response addresses the question.

A score of 0.70 is the project target. High scores on both metrics indicate a
grounded and relevant answer. Low Faithfulness suggests unsupported claims;
low Answer Relevancy suggests that the answer does not fully address the
question.

## 13. Execution evidence

Capture 3-5 screenshots from one live run. The exact checklist and filenames
are in `screenshots/README.md`. At minimum, show:

1. Application startup.
2. All three graph nodes firing in order.
3. Active MCP loading and retrieved sources.
4. `Backend: ragas` with both mandatory scores.
5. Final answer and score interpretation.

## 14. Submission checklist

- [ ] Run `pytest -q`.
- [ ] Complete one live Ollama + RAGAS execution.
- [ ] Add 3-5 genuine screenshots under `screenshots/`.
- [ ] Confirm the README commands work on the submission machine.
- [ ] Delete `.venv/`, `.env`, `chroma_db/`, logs, and temporary output.
- [ ] Confirm no API keys, passwords, tokens, or credentials are present.
- [ ] ZIP this project directory and upload it using the supplied portal guide.

