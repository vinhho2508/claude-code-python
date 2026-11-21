from app.tools.registry import tool

from enum import Enum

class LSPOperation(Enum):
    GO_TO_DEFINITION = "goToDefinition"

@tool(
    name="LSP",
    description=" Returns the file, line, and character where a symbol is defined.",
    parameters={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["goToDefinition"]
            },
            "filePath": {
                "type": "string",
                "description": "Absolute path, or a path relative to the agent's current working directory"
            },
            "line": {
                "type": "integer",
                "minimum": 1,
                "description": "1-based line number of the symbol."
            },
            "character": {
                "type": "integer",
                "minimum": 1,
                "description": "1-based charactrer offset in UTF-16 code units (same as character count for ASCII)."
            },
        },
        "required": ["operation", "filePath", "line", "character"]
    }
)
def lsp(operation: LSPOperation, filePath: str, line: int, character: int) -> str:
    return "LSP is not implemented yet"