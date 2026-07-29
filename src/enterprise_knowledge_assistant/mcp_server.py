"""Filesystem MCP server exposing the approved knowledge directory."""

from pathlib import Path

from fastmcp import FastMCP

from enterprise_knowledge_assistant.config import Settings
from enterprise_knowledge_assistant.knowledge_security import safe_document_path


mcp = FastMCP("Enterprise Knowledge Filesystem Server")
KNOWLEDGE_DIR = Settings().knowledge_dir.resolve()


def _safe_document_path(filename: str) -> Path:
    """Resolve a filename while preventing access outside the knowledge base."""

    return safe_document_path(KNOWLEDGE_DIR, filename)


@mcp.tool
def list_knowledge_files() -> list[str]:
    """List Markdown and text files available to the assistant."""

    return sorted(
        path.name
        for path in KNOWLEDGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    )


@mcp.tool
def read_knowledge_file(filename: str) -> str:
    """Read one approved knowledge file by filename."""

    document_path = _safe_document_path(filename)
    if not document_path.exists():
        raise FileNotFoundError(f"Knowledge file not found: {filename}")
    return document_path.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()
