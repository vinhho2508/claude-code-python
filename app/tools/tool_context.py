from dataclasses import dataclass

from app.llm import LLM
from app.lsp_session import LSPSession

@dataclass(frozen=True)
class ToolContext:
    llm: LLM
    lsp: LSPSession | None = None