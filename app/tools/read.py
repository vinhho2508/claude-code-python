from pathlib import Path
from app.tools.registry import tool

@tool(
        name="Read",
        description="Read a file",
        parameters= {
            "type": "object", 
            "properties": { 
                "file_path": {
                    "type": "string",
                    "description": "Path to the file"
                },
            },
            "required": ["file_path"]
        }
)
def read_file(file_path: str) -> str:
    try:
        return Path(file_path).expanduser().read_text(encoding="utf-8")
    except OSError as e:
        return f"Error reading {file_path}: {e}"
    
# READ = Tool(
#     name="Read",
#     description="Read a file",
#     parameters={
#         "type": "object",
#         "properties": {
#             "file_path": {"type": "string", "description": "The path to the file to read"},
#         },
#         "required": ["file_path"]
#     },
#     handler=read_file
# )