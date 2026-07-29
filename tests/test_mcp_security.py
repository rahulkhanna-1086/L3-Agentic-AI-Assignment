import pytest
from pathlib import Path

from enterprise_knowledge_assistant.knowledge_security import safe_document_path


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge_base"


def test_mcp_server_rejects_parent_directory_access():
    with pytest.raises(ValueError):
        safe_document_path(KNOWLEDGE_DIR, "../secret.txt")


def test_mcp_server_rejects_unsupported_extensions():
    with pytest.raises(ValueError):
        safe_document_path(KNOWLEDGE_DIR, "program.py")
