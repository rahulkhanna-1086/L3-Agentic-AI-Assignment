# Enterprise Knowledge Assistant Architecture

This document describes the current proof-of-concept architecture and a
production-ready evolution suitable for an internal enterprise platform.

## Start here: simplified animated flow

The animation below highlights one stage at a time and is intended for project
demonstrations and manager presentations.

![Animated Enterprise Knowledge Assistant flow](architecture-flow.gif)

The remaining diagrams provide deeper technical detail for engineering and
architecture discussions.

## 1. Current solution architecture

```mermaid
flowchart TB
    User["Employee / Business User"]

    subgraph Experience["User Experience Layer"]
        UI["Streamlit Chat Interface<br/>Multi-question conversation<br/>Live/demo mode<br/>Sources and RAGAS scores<br/>Expandable execution trace"]
        CLI["Command-line Interface<br/>Interactive questions<br/>Single-question execution"]
    end

    subgraph Orchestration["Agent Orchestration - LangGraph"]
        Start(("Start"))
        Retriever["Retriever Agent<br/>Requests approved documents through MCP<br/>Builds or reuses vector index<br/>Retrieves relevant chunks"]
        Response["Response Agent<br/>Combines question and context<br/>Generates grounded response<br/>Refuses unsupported answers"]
        Evaluator["Evaluator Agent<br/>Runs RAGAS evaluation<br/>Calculates Faithfulness<br/>Calculates Answer Relevancy<br/>Produces interpretation"]
        Decision{"Scores at least 0.70<br/>or retry limit reached?"}
        End(("End"))

        Start --> Retriever
        Retriever --> Response
        Response --> Evaluator
        Evaluator --> Decision
        Decision -- "Yes" --> End
        Decision -- "No: retrieve more context" --> Retriever
    end

    subgraph Integration["Integration Layer - MCP"]
        MCPClient["FastMCP Client<br/>Used by Retriever Agent"]
        MCPServer["Filesystem MCP Server<br/>list_knowledge_files<br/>read_knowledge_file<br/>Path traversal protection<br/>File-type restrictions"]
    end

    subgraph RAG["Retrieval-Augmented Generation Layer"]
        Loader["LangChain Documents"]
        Chunker["Recursive Character Splitter<br/>500-character chunks<br/>100-character overlap"]
        Embeddings["Ollama Embeddings<br/>nomic-embed-text"]
        VectorDB[("Chroma Vector Database<br/>Persistent semantic index")]
        Search["Similarity Search<br/>Top 4 relevant chunks"]
    end

    subgraph Intelligence["Model and Evaluation Layer"]
        LLM["Ollama Chat Model<br/>gpt-oss:120b-cloud"]
        RAGAS["RAGAS Evaluator<br/>Faithfulness<br/>Answer Relevancy"]
    end

    subgraph Knowledge["Approved Knowledge Base"]
        Leave["Employee Leave Policy"]
        Flexible["Flexible Work Policy"]
        Resignation["Resignation Policy"]
    end

    subgraph Observability["Observability and Evidence"]
        Console["Console Logs"]
        LogFiles["Timestamped Execution Logs"]
        Results["latest_result.json"]
        Trace["Node Input/Output Trace"]
    end

    User --> UI
    User --> CLI
    UI --> Start
    CLI --> Start

    Retriever --> MCPClient
    MCPClient --> MCPServer
    MCPServer --> Leave
    MCPServer --> Flexible
    MCPServer --> Resignation

    MCPServer --> Loader
    Loader --> Chunker
    Chunker --> Embeddings
    Embeddings --> VectorDB
    Retriever --> Search
    Search --> VectorDB
    Search --> Retriever

    Response --> LLM
    Evaluator --> RAGAS
    RAGAS --> LLM
    RAGAS --> Embeddings

    Retriever -. "Input/output events" .-> Trace
    Response -. "Input/output events" .-> Trace
    Evaluator -. "Input/output events" .-> Trace
    Trace --> Console
    Trace --> LogFiles
    End --> Results
    End --> UI
    End --> CLI
```

## 2. Request execution sequence

```mermaid
sequenceDiagram
    autonumber

    actor Employee
    participant UI as Streamlit UI
    participant LG as LangGraph
    participant RA as Retriever Agent
    participant MCP as Filesystem MCP Server
    participant KB as Policy Documents
    participant VDB as Chroma Vector DB
    participant OA as Ollama
    participant EA as RAGAS Evaluator

    Employee->>UI: Ask a policy question
    UI->>LG: Submit question
    LG->>RA: Start retrieval

    alt Vector index not initialized
        RA->>MCP: list_knowledge_files()
        MCP->>KB: Discover approved documents
        KB-->>MCP: Approved filenames
        RA->>MCP: read_knowledge_file()
        MCP->>KB: Read validated documents
        KB-->>MCP: Document contents
        MCP-->>RA: LangChain documents
        RA->>RA: Split documents into chunks
        RA->>OA: Generate chunk embeddings
        OA-->>RA: Embedding vectors
        RA->>VDB: Store vectors and metadata
    end

    RA->>OA: Embed user question
    OA-->>RA: Question vector
    RA->>VDB: Semantic similarity search
    VDB-->>RA: Top relevant chunks and sources
    RA-->>LG: Retrieved context

    LG->>OA: Question plus retrieved context
    OA-->>LG: Grounded answer

    LG->>EA: Question, answer and contexts
    EA->>OA: Judge answer claims and relevance
    OA-->>EA: Evaluation results
    EA-->>LG: Faithfulness and relevancy scores

    alt Scores meet threshold
        LG-->>UI: Answer, sources, scores and trace
        UI-->>Employee: Display evaluated response
    else Scores below threshold and retry available
        LG->>RA: Retry with more context
        RA->>VDB: Retrieve additional chunks
        VDB-->>RA: Expanded context
        RA-->>LG: New context
        LG->>OA: Regenerate grounded answer
        OA-->>LG: Improved answer
        LG->>EA: Re-evaluate answer
        EA-->>LG: Updated scores
        LG-->>UI: Final evaluated response
        UI-->>Employee: Display answer and evidence
    end
```

## 3. Current component responsibilities

| Component | Responsibility |
|---|---|
| Streamlit UI | Provides chat history, execution mode selection, answers, sources, scores, interpretation and trace details |
| Command-line interface | Supports interactive terminal questions and automated single-question execution |
| LangGraph | Controls the agent workflow, state transitions and conditional retry |
| Retriever Agent | Loads approved documents through MCP, builds the index and retrieves relevant context |
| Response Agent | Generates concise answers using only retrieved context |
| Evaluator Agent | Runs mandatory RAGAS metrics and interprets the results |
| FastMCP Server | Provides controlled access to approved knowledge files |
| RAG service | Performs chunking, embedding, vector storage and similarity retrieval |
| Chroma | Stores document vectors and source metadata |
| Ollama | Supplies the generation and embedding models |
| RAGAS | Measures Faithfulness and Answer Relevancy |
| Observability | Records node inputs, node outputs, routing decisions and final results |

## 4. Production-ready enterprise architecture

```mermaid
flowchart TB
    subgraph Channels["Enterprise Access Channels"]
        Web["Internal Web Portal"]
        Teams["Microsoft Teams Bot"]
        ServiceDesk["Service Desk Assistant"]
        App["Existing Business Application"]
        APIConsumer["Internal APIs"]
    end

    subgraph Security["Identity and Security"]
        SSO["Microsoft Entra ID / SSO"]
        RBAC["Role-Based Access Control"]
        Policy["Document-Level Permissions"]
        Guardrails["Prompt and Content Guardrails"]
        DLP["DLP / Sensitive Data Controls"]
    end

    subgraph Gateway["Application and API Layer"]
        GatewayAPI["Enterprise API Gateway"]
        ChatAPI["Knowledge Assistant API"]
        Session["Conversation and Session Manager"]
        Feedback["User Feedback Service"]
    end

    subgraph AgentPlatform["Agentic AI Platform - LangGraph"]
        Router["Intent and Domain Router"]
        RetrieverAgent["Retriever Agent"]
        ResponseAgent["Response Agent"]
        EvaluatorAgent["Evaluator Agent"]
        ActionAgent["Optional Action Agent<br/>Creates tickets or workflow requests"]
        HumanReview["Human Approval Node<br/>For high-risk actions"]
    end

    subgraph MCPFabric["MCP Integration Fabric"]
        MCPGateway["Managed MCP Gateway"]
        SharePointMCP["SharePoint MCP"]
        JiraMCP["Jira MCP"]
        GitHubMCP["GitHub MCP"]
        DBMCP["Database / SQL MCP"]
        ServiceNowMCP["ServiceNow MCP"]
        CustomMCP["Project-Specific MCP Servers"]
    end

    subgraph KnowledgePipeline["Enterprise Knowledge Pipeline"]
        Connectors["Source Connectors"]
        Extract["Extract and Normalize"]
        Classification["Security Classification"]
        Chunking["Semantic Chunking"]
        Embed["Enterprise Embedding Model"]
        Metadata["Metadata and Permission Mapping"]
        EnterpriseVector[("Enterprise Vector Database")]
        Refresh["Scheduled and Event-Driven Refresh"]
    end

    subgraph EnterpriseSources["Enterprise Information Sources"]
        SharePoint["SharePoint / OneDrive"]
        Confluence["Confluence"]
        Policies["Policies and Procedures"]
        Jira["Jira Projects"]
        GitHub["GitHub Repositories"]
        Database["Operational Databases"]
        ServiceNow["ServiceNow / Ticketing"]
        CRM["CRM and Customer Systems"]
    end

    subgraph ModelLayer["Model Gateway"]
        ModelRouter["Model Router"]
        LocalLLM["Private / Locally Hosted LLM"]
        CloudLLM["Approved Cloud LLM"]
        EmbeddingModel["Embedding Model"]
        SafetyModel["Safety and Classification Model"]
    end

    subgraph Governance["Governance, Quality and Operations"]
        RAGASProd["Continuous RAG Evaluation<br/>Faithfulness<br/>Answer Relevancy<br/>Context Precision<br/>Context Recall"]
        Tracing["LangSmith / OpenTelemetry Tracing"]
        Audit["Immutable Audit Logs"]
        Monitoring["Latency, Cost and Error Monitoring"]
        FeedbackAnalytics["Feedback and Adoption Analytics"]
        PromptRegistry["Versioned Prompt Registry"]
        EvalDataset["Golden Evaluation Dataset"]
    end

    Web --> GatewayAPI
    Teams --> GatewayAPI
    ServiceDesk --> GatewayAPI
    App --> GatewayAPI
    APIConsumer --> GatewayAPI

    SSO --> GatewayAPI
    GatewayAPI --> RBAC
    RBAC --> ChatAPI
    Policy --> RetrieverAgent
    Guardrails --> ChatAPI
    DLP --> ResponseAgent

    ChatAPI --> Session
    Session --> Router
    Router --> RetrieverAgent
    RetrieverAgent --> ResponseAgent
    ResponseAgent --> EvaluatorAgent
    EvaluatorAgent --> ChatAPI
    Router --> ActionAgent
    ActionAgent --> HumanReview
    HumanReview --> MCPGateway

    RetrieverAgent --> MCPGateway
    MCPGateway --> SharePointMCP
    MCPGateway --> JiraMCP
    MCPGateway --> GitHubMCP
    MCPGateway --> DBMCP
    MCPGateway --> ServiceNowMCP
    MCPGateway --> CustomMCP

    SharePointMCP --> SharePoint
    JiraMCP --> Jira
    GitHubMCP --> GitHub
    DBMCP --> Database
    ServiceNowMCP --> ServiceNow
    CustomMCP --> CRM

    SharePoint --> Connectors
    Confluence --> Connectors
    Policies --> Connectors
    Jira --> Connectors
    GitHub --> Connectors
    Database --> Connectors
    ServiceNow --> Connectors
    CRM --> Connectors

    Connectors --> Extract
    Extract --> Classification
    Classification --> Chunking
    Chunking --> Embed
    Embed --> Metadata
    Metadata --> EnterpriseVector
    Refresh --> Connectors
    EnterpriseVector --> RetrieverAgent

    ResponseAgent --> ModelRouter
    EvaluatorAgent --> ModelRouter
    Embed --> EmbeddingModel
    ModelRouter --> LocalLLM
    ModelRouter --> CloudLLM
    Guardrails --> SafetyModel

    ChatAPI --> Feedback
    AgentPlatform -. "Traces and metrics" .-> Tracing
    EvaluatorAgent --> RAGASProd
    GatewayAPI --> Audit
    MCPGateway --> Audit
    ModelRouter --> Monitoring
    Feedback --> FeedbackAnalytics
    PromptRegistry --> AgentPlatform
    EvalDataset --> RAGASProd
```

## 5. Enterprise architecture layers

| Layer | Purpose | Business value |
|---|---|---|
| Experience | Web, Teams, APIs and existing applications | Users access knowledge from tools they already use |
| Identity and security | SSO, roles, document permissions and DLP | Users only receive information they are permitted to see |
| Agent orchestration | Coordinates retrieval, generation, evaluation and actions | Produces controlled, auditable agent behaviour |
| MCP integration | Provides a standard interface to enterprise systems | New sources and actions can be added without redesigning the agent |
| Knowledge pipeline | Ingests, chunks, embeds and indexes enterprise content | Converts disconnected content into searchable organizational knowledge |
| Model gateway | Selects an approved local or cloud model | Controls data residency, cost and model flexibility |
| Evaluation | Measures answer grounding and relevance | Reduces hallucination risk and provides measurable quality |
| Observability | Captures traces, feedback, latency, failures and cost | Enables support, compliance and continual improvement |

## 6. Recommended business use cases

### Project knowledge assistant

Search architecture documents, coding standards, release procedures, project
decisions and operational instructions.

### Production-support assistant

Retrieve runbooks, known-error articles, previous incidents and troubleshooting
steps to reduce diagnosis time.

### Employee policy assistant

Answer questions about HR policies, leave, travel, compliance and internal
procedures.

### Service desk copilot

Suggest resolutions from historical tickets and create a support ticket when
human assistance is required.

### Developer onboarding assistant

Explain repository structure, local setup, coding standards, deployment
processes, team responsibilities and service ownership.

### Audit and compliance assistant

Retrieve approved procedures with exact sources and record the supporting
evidence used for every response.

## 7. Manager-level value proposition

The solution provides a governed conversational layer over fragmented
enterprise knowledge. Unlike a basic chatbot, it retrieves approved evidence,
generates a grounded response, measures response quality, records the execution
path and can securely connect to enterprise systems through MCP.

Key differentiators:

- Answers include evidence and source documents.
- RAGAS provides measurable quality instead of relying only on user perception.
- LangGraph makes the workflow controlled, observable and extensible.
- MCP provides a reusable integration standard.
- The model can remain local or be routed to an approved cloud provider.
- The same architecture can progress from answering questions to performing
  approved business actions.

## 8. Suggested implementation roadmap

### Phase 1 - Focused proof of value

- Select one high-value, low-risk project knowledge domain.
- Connect a limited set of approved documents.
- Define 30-50 representative questions and expected answers.
- Measure answer quality, response time and user satisfaction.
- Keep the assistant read-only.

### Phase 2 - Controlled pilot

- Add enterprise authentication and role-based access.
- Integrate SharePoint, Confluence, Jira or the relevant project repository.
- Introduce document-level permission filtering.
- Add feedback collection and operational dashboards.
- Establish content ownership and refresh schedules.

### Phase 3 - Production platform

- Deploy behind the enterprise API gateway.
- Add centralized model routing, audit logs and DLP controls.
- Establish golden evaluation datasets and release quality gates.
- Add high availability, monitoring and support processes.
- Expand to additional business domains.

### Phase 4 - Governed actions

- Add action agents for approved workflows such as ticket creation.
- Require human approval for sensitive or high-impact operations.
- Apply least-privilege MCP permissions.
- Audit every action, input, approval and external-system response.

## 9. Success measures

Recommended pilot measures include:

- Percentage of questions answered with sufficient evidence.
- Faithfulness and Answer Relevancy scores.
- Reduction in time spent searching for information.
- Reduction in repeated service desk or subject-matter-expert questions.
- User satisfaction and answer acceptance rate.
- Number of unanswered questions caused by missing content.
- Response latency and model operating cost.
- Security, permission and audit exceptions.

## 10. Key production considerations

- Enforce the source system's access permissions during retrieval.
- Treat retrieved content as untrusted and protect against prompt injection.
- Avoid placing secrets, credentials or sensitive personal data in prompts.
- Maintain document ownership, versioning and refresh processes.
- Log source references, model versions, prompts, scores and routing decisions.
- Use human approval before the assistant changes enterprise data.
- Maintain an evaluation dataset representing real project questions.
- Review model and embedding changes through measured quality gates.
