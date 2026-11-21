from dataclasses import dataclass

from app.llm import LLM

@dataclass(frozen=True)
class ToolContext:
    llm: LLM