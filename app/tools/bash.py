import os
import signal
import subprocess
import sys

from app.tools.registry import tool

MAX_OUTPUT_LENGTH = 10_000
EXECUTION_TIMEOUT = 30
KILL_GRACE_TIMEOUT = 5


def _truncate(output: str) -> str:
    """Keep the head and tail of long output, noting how much was dropped."""
    if len(output) <= MAX_OUTPUT_LENGTH:
        return output
    half = MAX_OUTPUT_LENGTH // 2
    omitted = len(output) - 2 * half
    return f"{output[:half]}\n... [{omitted} characters truncated] ...\n{output[-half:]}"


@tool(
    name="Bash",
    description=(
        "Execute a shell command and return its exit code and combined stdout/stderr. "
        f"Commands are killed after {EXECUTION_TIMEOUT} seconds and output is truncated "
        f"to {MAX_OUTPUT_LENGTH} characters."
    ),
    parameters={
        "type": "object",
        "required": ["command"],
        "properties": {
            "command": {
                "type": "string",
                "description": "The command to execute"
            }
        }
    }
)
def bash(command: str) -> str:
    """Run a command in bash; return its exit code and combined output (truncated, with timeout)."""
    try:
        proc = subprocess.Popen(
            ["bash", "-c", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            errors="replace",
            start_new_session=True,
        )
    except OSError as e:
        return f"Error executing command: {e}"

    try:
        output, _ = proc.communicate(timeout=EXECUTION_TIMEOUT)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            print(f"Process group {proc.pid} already exited before kill", file=sys.stderr)

        try:
            output, _ = proc.communicate(timeout=KILL_GRACE_TIMEOUT)
        except subprocess.TimeoutExpired:
            output = "(output unavailable: process did not exit after kill)"

        output = f"Timed out after {EXECUTION_TIMEOUT} seconds\n{output}"

    return f"Return code: {proc.returncode}\n{_truncate(output)}"
