import os
import time
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
        self.cursor = 0                                  # notification queue position
        self.last_report: dict[str, set[tuple]] = {}     # uri -> issue keys in the latest accepted report
        self.pending: dict[str, list[dict]] = {}         # uri -> new issues not yet given to the model

    # Bounded wait for the server's report after each didOpen/didChange.
    REPORT_TIMEOUT_S = 1.0

    @staticmethod
    def _issue_key(d: dict) -> tuple:
        start = d.get("range", {}).get("start", {})
        return (d.get("severity"), start.get("line"), start.get("character"), d.get("message"))

    def _accept_report(self, uri: str, diagnostics: list[dict]) -> None:
        """Process one current report, in arrival order.

        Issues absent from the previous report for this file become pending, so an
        error is still shown even if a later report in the same turn clears it.
        """
        previous = self.last_report.get(uri, set())
        queued = self.pending.setdefault(uri, [])
        queued_keys = {self._issue_key(d) for d in queued}
        for d in diagnostics:
            key = self._issue_key(d)
            if key not in previous and key not in queued_keys:
                queued.append(d)
                queued_keys.add(key)
        # An empty report clears the file, so a returning issue counts as new again.
        self.last_report[uri] = {self._issue_key(d) for d in diagnostics}

    def _drain(self, timeout_ms: int = 0) -> set[str]:
        """Read one batch; judge each report against the versions sent so far.

        Returns the URIs that received a current report in this batch.
        """
        response = self.client.notifications(after=self.cursor, timeout_ms=timeout_ms)
        # Advance for every batch, even empty or unrelated ones.
        self.cursor = response.get("cursor", self.cursor)

        reported = set()
        for note in response.get("notifications", []):
            if note.get("method") != "textDocument/publishDiagnostics":
                continue
            params = note.get("params", {})
            uri = params.get("uri")
            version = params.get("version")
            if version is not None and version != self.versions.get(uri):
                continue  # stale: older (or never sent) version
            self._accept_report(uri, params.get("diagnostics", []))
            reported.add(uri)
        return reported

    def _send_document(self, method: str, params: dict, uri: str, version: int) -> None:
        """didOpen/didChange with diagnostics bookkeeping around it.

        1. Drain first, so queued reports are judged against the pre-change version.
        2. Send, then record the version (only after the notification succeeded).
        3. Wait (bounded) for this document's report, so it is judged while still current.
        """
        self._drain(0)
        self.client.notify(method, params)
        self.versions[uri] = version

        deadline = time.monotonic() + self.REPORT_TIMEOUT_S
        while True:
            remaining_ms = int((deadline - time.monotonic()) * 1000)
            if remaining_ms <= 0:
                return
            if uri in self._drain(min(remaining_ms, 5000)):
                break
        # Reports for other open files follow right after; pick up what has arrived.
        self._drain(0)

    def take_new_diagnostics(self) -> str | None:
        """Drain the queue; return pending issues formatted for the model, then clear them."""
        self._drain(0)

        sections = []
        for uri, issues in self.pending.items():
            if not issues:
                continue
            issues.sort(key=lambda d: (d["range"]["start"]["line"], d["range"]["start"]["character"]))
            lines = [f"{uri_to_relative_path(uri, self.cwd)}:"]
            for d in issues:
                start = d["range"]["start"]
                lines.append(f"  [Line {start['line'] + 1}:{start['character'] + 1}] {d['message']}")
            sections.append("\n".join(lines))
        self.pending.clear()

        if not sections:
            return None
        return ("<new-diagnostics>The following new diagnostic issues were detected:\n\n"
                + "\n\n".join(sections)
                + "</new-diagnostics>")

    def language_id(self, file_path: str) -> str | None:
        return self.client.extension_to_language.get(Path(file_path).suffix)
    
    def _open(self, uri: str, language_id: str, text: str) -> None:
        self._send_document("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": text,
            }
        }, uri, 1)

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

        self._send_document("textDocument/didChange", {
            "textDocument": {"uri": uri, "version": next_version},
            "contentChanges": [{"text": text}]
        }, uri, next_version)