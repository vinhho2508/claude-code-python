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

    def __init__(self, client: LSPClient, cwd: str | None = None):
        self.client = client
        self.cwd = cwd or os.getcwd()
        self.versions: dict[str, int] = {}  # uri -> version; presence == opened
        self.cursor = 0
        self.current: dict[str, list[dict]] = {}
        self.shown: dict[str, set[tuple]] = {}

    @staticmethod
    def _issue_key(d: dict) -> tuple:
        start = d["range"]["start"]
        return (d.get("serverity"), start["line"], start["character"], d["message"])

    def _drain_diagnostics(self) -> None:
        response = self.client.notifications(after=self.cursor, timeout_ms = 0)
        self.cursor = response.get("cursor", self.cursor)

        for note in response.get("notifications", []):
            if note.get("method") != "textDocument/publishDiagnostics":
                continue
            params = note["params"]
            uri = params["uri"]
            version = params.get("version")
            if version is not None and version != self.versions.get(uri):
                continue
            self.current[uri] = params.get("diagnostics", [])

    def take_new_diagnostics(self) -> str | None:
        self._drain_diagnostics()

        sections = []
        for uri, diagnostics in self.current.items():
            keys = {self._issue_key(d) for d in diagnostics}
            seen = self.shown.get(uri, set())

            new = [d for d in diagnostics if self._issue_key(d) not in seen]
            self.shown[uri] = keys

            if not new:
                continue
            new.sort(key=lambda d: (d["range"]["start"]["line"], d["range"]["start"]["character"]))
            lines = [f"{uri_to_relative_path(uri, self.cwd)}:"]
            for d in new:
                start = d["range"]["start"]
                lines.append(f"  [Linee {start['line'] + 1}: {start['character'] + 1}] {d['message']}")
            sections.append("\n".join(lines))
        
        if not sections:
            return None
        return ("<new-diagnostics> The following new diagnostic issues were detected:\n\n"
                + "\n\n".join(sections)
                + "</new-diagnostics>")

    def language_id(self, file_path: str) -> str | None:
        return self.client.extension_to_language.get(Path(file_path).suffix)
    
    def _open(self, uri: str, language_id: str, text: str) -> None:
        self.client.notify("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": text,
            }
        })
        self.versions[uri] = 1

    def ensure_open(self, file_path: str) -> str:
        """Send didOpen once per URI. Returns the URI."""
        uri = path_to_uri(file_path, self.cwd)
        if uri in self.versions:
            return uri

        language_id = self.language_id(file_path)
        if language_id is None:
            raise ValueError(f"unsupported file type: {file_path}")

        text = Path(self.cwd, file_path).resolve().read_text(encoding="utf-8")
        self._open(uri, language_id, text)
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
    
    def sync_saved(self, file_path: str, text: str) -> None:
        language_id = self.language_id(file_path)
        if language_id is None:
            return
        uri = path_to_uri(file_path, self.cwd)
        if uri not in self.versions:
            self._open(uri, language_id, text)
            return
        
        next_version = self.versions[uri] + 1

        self.client.notify("textDocument/didChange", {
            "textDocument": {"uri": uri, "version": next_version},
            "contentChanges": [{"text": text}]
        })

        self.versions[uri] = next_version