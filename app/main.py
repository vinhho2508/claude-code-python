import argparse
import sys

from app.agent import run_agent
from app.config import Settings
from app.llm import LLM
from app.lsp_client import LSPClient
from app.lsp_session import LSPSession
from app.skills import registry
from app.tools.tool_context import ToolContext

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", required=True, help="prompt")
    args = parser.parse_args()

    lsp_client = LSPClient.from_environment()
    lsp = LSPSession(lsp_client) if lsp_client else None
    if lsp:
        print(f"Connected to LSP server at {lsp_client.url}", file=sys.stderr)

    settings = Settings.from_env()
    registry.register_skills()

    ctx = ToolContext(llm=LLM(settings), lsp=lsp)
    print(run_agent(ctx, args.p))

if __name__ == "__main__":
    main()