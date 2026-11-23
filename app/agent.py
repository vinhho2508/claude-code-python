import sys
from app import tools
from app.llm import LLM
from app.skills.registry import format_skills_prompt, expand_skill_command

def _excluded(ctx: tools.ToolContext, extra=()) -> set[str]:
    excluded = set(extra)
    if ctx.lsp is None:
        excluded.add("LSP")
    return excluded

def run_loop(
    ctx: tools.ToolContext,
    messages: list[dict],
    tool_schemas: list[dict] | None = None,
    max_turns: int = 50,
) -> str:
    if tool_schemas is None:
        tool_schemas = tools.schemas(exclude=_excluded(ctx))

    for _ in range(max_turns):
        response = ctx.llm.chat(messages, tool_schemas)

        if not response.choices:
            raise RuntimeError("no choices in response")
        
        message = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls
        })

        if not message.tool_calls:
            return message.content or ""
        
        for call in message.tool_calls:
            result = tools.run_tool(call.function.name, call.function.arguments, ctx)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result })

        # Before the next model request: attach new current diagnostics
        # to the latest tool result.
        if ctx.lsp is not None:
            try:
                feedback = ctx.lsp.take_new_diagnostics()
            except (OSError, ValueError, RuntimeError) as e:
                feedback = None
                print(f"[lsp] diagnostics read failed: {e}", file=sys.stderr)
            if feedback:
                messages[-1]["content"] += "\n\n" + feedback
    raise RuntimeError(f"agent did not finish within {max_turns} turns")

def run_agent(ctx: tools.ToolContext, prompt: str) -> str:
    messages: list[dict] = []
    skills_prompt = format_skills_prompt()
    if skills_prompt:
        messages.append({"role": "system", "content": skills_prompt})

    
    # messages.append({"role": "user", "content": expand_skill_command(prompt)})
    for content in expand_skill_command(prompt):
        messages.append({"role": "user", "content": content})

    return run_loop(ctx, messages)


def run_subagent(ctx: tools.ToolContext, prompt: str) -> str:
    """Run the same loop over a fresh conversation holding only `prompt`.

    No skills catalog and no Skill tool, so a forked skill can't fork again.
    """
    messages = [{"role": "user", "content": prompt}]
    return run_loop(ctx, messages, tools.schemas(exclude=_excluded(ctx, {"Skill"})))
