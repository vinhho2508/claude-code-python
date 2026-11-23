#!/bin/sh
#
# Run the claude-code agent.
#
# Usage:
#   ./claude.sh -p "<prompt>"
#
# Requires OPENROUTER_API_KEY; optional OPENROUTER_BASE_URL, MODEL,
# CODECRAFTERS_LSP_URL (see README.md).

set -e # Exit early if any commands fail

SCRIPT_DIR="$(dirname "$0")"

# PYTHONSAFEPATH keeps the current directory off sys.path, so a file in the
# directory the agent is working in can't shadow one of our modules.
PYTHONSAFEPATH=1 PYTHONPATH="$SCRIPT_DIR" exec uv run \
  --project "$SCRIPT_DIR" \
  --quiet \
  -m app.main \
  "$@"
