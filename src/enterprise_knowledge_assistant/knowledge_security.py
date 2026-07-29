"""Path validation shared by the MCP server and security tests."""

from pathlib import Path


def safe_document_path(knowledge_dir: Path, filename: str) -> Path:
    """Resolve a filename while preventing access outside the knowledge base."""

    approved_directory = knowledge_dir.resolve()
    requested_path = (approved_directory / filename).resolve()
    if requested_path.parent != approved_directory:
        raise ValueError("Only files inside the knowledge base are allowed.")
    if requested_path.suffix.lower() not in {".md", ".txt"}:
        raise ValueError("Only Markdown and text knowledge files are allowed.")
    return requested_path

