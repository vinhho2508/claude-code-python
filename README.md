# claude-code-python

A minimal Claude Code–style AI coding agent written from scratch in Python.
Give it a prompt; it talks to an LLM over an OpenAI-compatible API, calls tools
to read, write, and run code, and loops until the task is done.

## Features

- **Agent loop**: sends the conversation and tool schemas to the model, runs every
  tool call it returns, appends the results, and repeats until the model answers
  without tool calls (capped at 50 turns).
- **Tools**, registered with a `@tool` decorator and auto-discovered from `app/tools/`:
  - `Read`: read a file.
  - `Write`: atomic file writes (temp file + `os.replace`, keeps the original permissions).
  - `Bash`: run a shell command with a 30s timeout, process-group kill, and
    head/tail output truncation.
  - `LSP`: `goToDefinition` and `findReferences` through a language server.
  - `Skill`: load a skill's instructions on demand.
- **Skills**: `.claude/skills/<name>/SKILL.md` files with YAML frontmatter.
  - Listed for the model in the system prompt.
  - Invocable as `/name args` slash commands, which can be chained.
  - Support `$ARGUMENTS`, `$0`, and `$ARGUMENTS[n]` placeholders.
  - `context: fork` runs the skill in an isolated subagent.
- **LSP diagnostics feedback**: after the agent writes a file, new language-server
  errors are attached to the tool result so the model can fix what it broke.

## Getting started

Requirements: Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```sh
export OPENROUTER_API_KEY=sk-...
./claude.sh -p "Create hello.py that prints hello world, then run it"
```

Configuration (environment variables):

| Variable | Default | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | — (required) | API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | Any OpenAI-compatible endpoint |
| `MODEL` | `anthropic/claude-haiku-4.5` | Model ID |
| `CODECRAFTERS_LSP_URL` | unset | HTTP bridge to a language server; enables the `LSP` tool and diagnostics |

## Project layout

```
app/
├── main.py          # CLI entry point (-p "<prompt>")
├── agent.py         # agent loop + subagent
├── llm.py           # OpenAI-compatible chat client
├── config.py        # settings from env
├── lsp_client.py    # HTTP client for the LSP bridge
├── lsp_session.py   # open/sync files, definition/references, diagnostics diffing
├── tools/           # tool registry + Read, Write, Bash, LSP, Skill
└── skills/          # SKILL.md discovery, parsing, argument substitution
tests/               # pytest suite
```

## Tests

```sh
uv run pytest
```
