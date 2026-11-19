from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path
    prompt: str = ""
