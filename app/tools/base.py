from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., str]

    def schema(self) -> dict:
        """Build the dict format the OpenAI API expects."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }