from pathlib import Path
from app.tools.registry import tool
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
        }
)
def skill_tool(name: str, args: str = "") -> str:
    skill = get_skill(name)
    if not skill:
        return f"Could not find the skill {name}"

    return substitute_arguments(skill.prompt, args)