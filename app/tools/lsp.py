from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse
from app.tools.registry import tool

from enum import Enum
from app.lsp_session import format_location, uri_to_relative_path
from app.tools.registry import tool
from app.tools.tool_context import ToolContext

class LSPOperation(Enum):
    GO_TO_DEFINITION = "goToDefinition"
    FIND_REFERENCES = "findReferences"

def format_references(references: list[dict], cwd: str) -> str:
    if not references:
        return "No references found."

    grouped = defaultdict(list)
    for ref in references:
        grouped[ref["uri"]].append(ref["range"]["start"])

    lines = [f"Found {len(references)} references across {len(grouped)} files:"]

    for uri, positions in grouped.items():
        # Convert 'file:///project/reports.py' -> relative path 'reports.py'

        lines.append(f"\n{uri_to_relative_path(uri, cwd)}:")
        for pos in positions:
            # Convert 0-based LSP indices to 1-based line and character
            lines.append(f"  Line {pos['line'] + 1}:{pos['character'] + 1}")

    return "\n".join(lines)

@tool(
    name="LSP",
    description=" Returns the file, line, and character where a symbol is defined." \
    "Write results may later be followed by a <new-diagnostics> block: these are " \
    "language-server errors (in any file) caused by your edits; fix them and re-check.",
    parameters={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["goToDefinition", "findReferences"]
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
            if not locations:
                return "No definition found"
            return "\n".join(f"Defined in {format_location(loc, ctx.lsp.cwd)}" for loc in locations)
        if op is LSPOperation.FIND_REFERENCES:
            references = ctx.lsp.references(filePath, line, character)
            if not references:
                return "No references found"
            return format_references(references, ctx.lsp.cwd)

    except (OSError, ValueError, RuntimeError) as e:
        return f"Error: {e}"
    
    return f"No matched LSP operation: {operation}"
