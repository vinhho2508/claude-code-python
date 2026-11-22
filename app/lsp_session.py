import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.lsp_client import LSPClient


def path_to_uri(file_path: str, cwd: str) -> str:
    """Resolve against cwd and build a percent-encoded file:// URI."""
    return Path(cwd, file_path).resolve().as_uri()


def uri_to_relative_path(uri: str, cwd: str) -> str:
    """file:///project/cart%20notes.py -> cart notes.py (relative to cwd)."""
    return os.path.relpath(unquote(urlparse(uri).path), cwd)


def format_location(location: dict, cwd: str) -> str:
    """LSP Location (0-based) -> 'path:line:char' (1-based)."""
    start = location["range"]["start"]
    path = uri_to_relative_path(location["uri"], cwd)
    return f"{path}:{start['line'] + 1}:{start['character'] + 1}"


class LSPSession:
    """Per-connection document state on top of the supplied client.

    The server remembers opened documents for the lifetime of the connection,
    so this state must live exactly as long as the client and be shared by
    every caller (main agent and subagents).
    """

    def __init__(self, client: LSPClient, cwd: str | None = None):
        self.client = client
        self.cwd = cwd or os.getcwd()
        self.versions: dict[str, int] = {}  # uri -> version; presence == opened

    def language_id(self, file_path: str) -> str | None:
        return self.client.extension_to_language.get(Path(file_path).suffix)

    def ensure_open(self, file_path: str) -> str:
        """Send didOpen once per URI. Returns the URI."""
        uri = path_to_uri(file_path, self.cwd)
        if uri in self.versions:
            return uri

        language_id = self.language_id(file_path)
        if language_id is None:
            raise ValueError(f"unsupported file type: {file_path}")

        text = Path(self.cwd, file_path).resolve().read_text(encoding="utf-8")
        self.client.notify("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": text,
            }
        })
        # Only mark as open after the notification succeeded.
        self.versions[uri] = 1
        return uri

    def definition(self, file_path: str, line: int, character: int) -> list[dict]:
        """1-based position in, list of LSP Locations out."""
        uri = self.ensure_open(file_path)
        result = self.client.request("textDocument/definition", {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character - 1},
        })
        if result is None:
            return []
        if isinstance(result, dict):
            result = [result]
        # LocationLink uses targetUri/targetSelectionRange; normalize to Location.
        return [
            {"uri": loc["targetUri"], "range": loc["targetSelectionRange"]}
            if "targetUri" in loc else loc
            for loc in result
        ]

    def references(self, file_path, line: int, character: int) -> list[dict]:
        uri=self.ensure_open(file_path)
        result = self.client.request("textDocument/references", {
            "textDocument": { "uri": uri},
            "position": { "line": line - 1, "character": character - 1},
            "context": { "includeDeclaration": True}
        })

        return result or []