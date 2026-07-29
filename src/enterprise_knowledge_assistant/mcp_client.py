"""Client used by the Retriever Agent to actively call the MCP server."""

from pathlib import Path
import os
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


class KnowledgeMCPClient:
    """Read knowledge documents through a local stdio MCP subprocess."""

    def __init__(self, server_path: Path):
        transport = StdioTransport(
            command=sys.executable,
            args=[str(server_path)],
            env=os.environ.copy(),
            cwd=str(server_path.parents[2]),
            keep_alive=False,
        )
        self.client = Client(transport)

    @staticmethod
    def _unwrap_text(result: object) -> str:
        """Extract text from FastMCP's tool result across compatible versions."""

        data = getattr(result, "data", None)
        if isinstance(data, str):
            return data

        content = getattr(result, "content", [])
        text_parts = [
            item.text
            for item in content
            if hasattr(item, "text") and isinstance(item.text, str)
        ]
        return "\n".join(text_parts)

    async def load_documents(self) -> dict[str, str]:
        """List and read all knowledge files using MCP tools."""

        async with self.client:
            list_result = await self.client.call_tool("list_knowledge_files", {})
            filenames = getattr(list_result, "data", None)

            if not isinstance(filenames, list):
                raw_text = self._unwrap_text(list_result)
                filenames = [
                    line.strip(" []'\"")
                    for line in raw_text.split(",")
                    if line.strip(" []'\"")
                ]

            documents: dict[str, str] = {}
            for filename in filenames:
                result = await self.client.call_tool(
                    "read_knowledge_file",
                    {"filename": filename},
                )
                documents[str(filename)] = self._unwrap_text(result)

        return documents
