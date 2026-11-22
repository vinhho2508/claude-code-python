from pathlib import Path
from app.tools.registry import tool
from app.tools.tool_context import ToolContext
from app.skills.skill import Skill
from app.skills.registry import get_skill, substitute_arguments

@tool(
        name="Skill",
        description="Load a skills's instructions into the conversation",
        parameters= {
            "type": "object", 
            "properties": { 
                "name": {
                    "type": "string",
                    "description": "The name of the skill to use"
                },
                "args": {
                    "type": "string",
                    "description": "Optional arguments for the skill"
                }
            },
            "required": ["name"]
        },
        need_context=True,
)
def skill_tool(name: str, args: str = "", ctx: ToolContext | None = None) -> str:
    skill = get_skill(name)
    if not skill:
        return f"Could not find the skill {name}"

    body = substitute_arguments(skill.prompt, args)
    if not skill.fork:
        return body

    if ctx is None:
        return f"Error: skill {name} needs a subagent but no context was provided"

    # Lazy import: app.agent imports app.tools, which imports this module at load time.
    from app.agent import run_subagent
    answer = run_subagent(ctx, body)
    return f"Skill {name} ran in a separate context and returned: {answer}"