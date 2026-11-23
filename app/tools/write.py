from pathlib import Path
from app.tools.registry import tool
import tempfile
import os
import shutil

from app.tools.tool_context import ToolContext


@tool(
        name="Write",
        description="Write content to a file",
        parameters={
            "type": "object",
            "properties":{
                "file_path": {
                    "type": "string",
                    "description": "Path to the file"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        },
        need_context=True
)
def write_file(file_path: str, content: str, ctx: ToolContext | None = None) -> str:
    """ Write file content to file_path.
        Returns: a message
    """

    lsp = ctx.lsp if ctx else None
    base = Path(lsp.cwd) if lsp else Path.cwd()

    path = Path(file_path).expanduser()
    if not path.is_absolute():
        path = base / path # Resolve absulute path into relative path
    if path.is_dir():
        return "Error: file_path is a directory"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        # temp file in the SAME directory so os.replace stays on one filesystem
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            if path.exists():
                shutil.copymode(path, tmp_name) # keep original permissions
            os.replace(tmp_name, path) # atomic swap
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True) # clean up the temp file
            raise
    except OSError as e:
        return f"Error writing {path}: {e}"
    result = f"Wrote {len(content.encode('utf-8'))} bytes to {path}"

    if lsp is not None:
        try:
            lsp.sync_saved(str(path), content)
        except (OSError, ValueError, RuntimeError) as e:
            result += f"\nWarning: language server sync failed: {e}"
    return result
