from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path
    prompt: str = ""
    fork: bool = False  # frontmatter `context: fork` → run body in a subagent
