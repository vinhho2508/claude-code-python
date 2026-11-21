from app.skills.skill import Skill
import yaml
from pathlib import Path
import re

_REGISTRY: dict[str, Skill] = {}

SKILL_PATH=".claude/skills"
SKILL_FILENAME="SKILL.md"

def get_all_skills_path(skill_dir: str=SKILL_PATH) -> list[Path]:
    directory = Path(skill_dir)
    if not directory.is_dir():
        return []

    skill_paths = [p / SKILL_FILENAME for p in sorted(directory.iterdir()) if (p / SKILL_FILENAME).is_file()]

    return skill_paths

def parse_skill(path: Path, default_name: str) -> Skill | None:
    content = path.read_text(encoding='utf-8')
    content = content.lstrip("﻿").lstrip()
    if not content.startswith("---"):
        return None

    parts = content.split('---', maxsplit=2)
    if len(parts) < 3:
        return None

    frontmatter = yaml.safe_load(parts[1]) or {}
    if not isinstance(frontmatter, dict):
        return None

    return Skill(
        name=frontmatter.get('name') or default_name,
        description=frontmatter.get('description') or "",
        path=path,
        prompt=parts[2].strip(),
        fork=frontmatter.get('context') == "fork")

def register_skills(skill_dir: str=SKILL_PATH) -> None:
    _REGISTRY.clear()
    all_paths = get_all_skills_path(skill_dir)

    for p in all_paths:
        skill = parse_skill(p, p.parent.name)
        if skill:
            _REGISTRY[skill.name] = skill

def format_skills_prompt() -> str:
    if not _REGISTRY:
        return ""

    lines = [f"- {v.name}: {v.description}" for v in _REGISTRY.values()]
    return "You have access to the following skills:\n\n" + "\n".join(lines)

# SKILL_NAME_COMMAND = re.compile(r"(?<!\S)/([\w-]+)(?!\S)")
_PLACEHOLDER = re.compile(r"\$ARGUMENTS\[(\d+)\]|\$ARGUMENTS|\$(\d+)")

def substitute_arguments(body: str, arguments: str) -> str:
    args = arguments.split()
    def replace(match: re.Match) -> str:
        if match.group(0) == "$ARGUMENTS":
            return arguments
        index = int(match.group(1) or match.group(2))
        return args[index] if index < len(args) else ""
    
    result, count = _PLACEHOLDER.subn(replace, body)
    if arguments and count == 0:
        result += f"\n\nARGUMENTS: {arguments}"
    return result

def get_skill(name: str) -> Skill | None:
    return _REGISTRY.get(name)

def expand_skill_command(prompt: str) -> list[str]:
    skills: list[Skill] = []
    rest = prompt.strip()
    while rest:
        head, *tail = rest.split(maxsplit=1)
        skill = get_skill(head[1:]) if head.startswith("/") else None
        if skill is None:
            break
        skills.append(skill)
        rest = tail[0] if tail else ""
    if not skills:
        return [prompt]
    return [substitute_arguments(s.prompt, rest) for s in skills]

# def expand_skill_command(prompt: str) -> str:
#     def replace(match: re.Match) -> str:
#         skill = get_skill(match.group(1))
#         if skill is None:
#             return match.group(0)
#         return skill.prompt
#     return SKILL_NAME_COMMAND.sub(replace, prompt)
