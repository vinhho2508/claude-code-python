from app.tools.registry import tool

from enum import Enum
from app.lsp_session import format_location
from app.tools.registry import tool
from app.tools.tool_context import ToolContext

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
    },
    need_context=True
)
def lsp(operation: LSPOperation, filePath: str, line: int, character: int, ctx: ToolContext | None = None) -> str:
    if ctx is None or ctx.lsp is None:
        return "Error: LSP is not configured"
    
    try:
        op = LSPOperation(operation)
    except ValueError:
        return f"Error: unsupported operation {operation!r}"
    
    try:
        if op is LSPOperation.GO_TO_DEFINITION:
            locations = ctx.lsp.definition(filePath, line, character)
    except (OSError, ValueError, RuntimeError) as e:
        return f"Error: {e}"
    
    if not locations:
        return "No definition found"
    return "\n".join(f"Defined in {format_location(loc, ctx.lsp.cwd)}" for loc in locations)