from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass(frozen=True)
class Skill:
    name: str
    description: str

SKILL_PATH=".claude/skills"
SKILL_FILENAME="SKILL.md"

def get_all_skills_path(skill_dir: str=SKILL_PATH) -> list[Path]:
    directory = Path(skill_dir)
    if not directory.is_dir():
        return []

    skill_paths = [p / SKILL_FILENAME for p in sorted(directory.iterdir()) if (p / SKILL_FILENAME).is_file()]

    return skill_paths

def parse_skill(content: str, default_name: str) -> Skill | None:
    content = content.lstrip("﻿").lstrip()
    if not content.startswith("---"):
        return None

    parts = content.split('---', maxsplit=2)
    if len(parts) < 3:
        return None

    frontmatter = yaml.safe_load(parts[1]) or {}
    return Skill(frontmatter.get('name') or default_name, frontmatter.get('description') or "")

def get_skills(skill_dir: str=SKILL_PATH) -> list[Skill]:
    all_skills: list[Skill] = []
    all_paths = get_all_skills_path(skill_dir)

    for p in all_paths:
        skill_content = p.read_text(encoding='utf-8')
        skill = parse_skill(skill_content, p.parent.name)
        if skill:
            all_skills.append(skill)

    return all_skills

def format_skills_prompt(skills: list[Skill]) -> str:
    if not skills:
        return ""

    lines = [f"- {s.name}: {s.description}" for s in skills]
    return "You have access to the following skills:\n\n" + "\n".join(lines)
