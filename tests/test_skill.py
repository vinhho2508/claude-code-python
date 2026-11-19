from app.skills.skill import Skill
from app.skills.registry import _REGISTRY, register_skills, format_skills_prompt, expand_skill_command

def write_skill(root, folder, content):
    d = root / folder
    d.mkdir()
    (d / "SKILL.md").write_text(content)
    return d / "SKILL.md"

def test_missing_dir_registers_nothing(tmp_path):
    register_skills(str(tmp_path / "nope"))
    assert _REGISTRY == {}
    assert format_skills_prompt() == ""

def test_registers_skills_and_skips_folders_without_skill_md(tmp_path):
    b = write_skill(tmp_path, "b", "---\nname: beta\ndescription: second\n---\nbody b")
    a = write_skill(tmp_path, "a", "---\nname: alpha\ndescription: first\n---\nbody a")
    (tmp_path / "empty").mkdir()
    register_skills(str(tmp_path))
    assert _REGISTRY == {"alpha": Skill("alpha", "first", a, "body a"),
                         "beta": Skill("beta", "second", b, "body b")}

def test_name_falls_back_to_folder(tmp_path):
    write_skill(tmp_path, "deploy", "---\ndescription: ship it\n---\n")
    register_skills(str(tmp_path))
    assert list(_REGISTRY) == ["deploy"]

def test_skips_file_without_frontmatter(tmp_path):
    write_skill(tmp_path, "x", "just text")
    register_skills(str(tmp_path))
    assert _REGISTRY == {}

def test_register_clears_previous_skills(tmp_path):
    write_skill(tmp_path, "a", "---\nname: alpha\n---\n")
    register_skills(str(tmp_path))
    register_skills(str(tmp_path / "nope"))
    assert _REGISTRY == {}

def test_format_prompt(tmp_path):
    write_skill(tmp_path, "a", "---\nname: alpha\ndescription: first\n---\n")
    register_skills(str(tmp_path))
    assert format_skills_prompt().endswith("- alpha: first")

def test_expand_replaces_command_and_keeps_rest(tmp_path):
    write_skill(tmp_path, "review", "---\nname: review\n---\nREVIEW IT")
    register_skills(str(tmp_path))
    assert expand_skill_command("please /review app.py") == "please REVIEW IT app.py"

def test_expand_multiple_commands(tmp_path):
    write_skill(tmp_path, "a", "---\nname: a\n---\nAAA")
    write_skill(tmp_path, "b", "---\nname: b\n---\nBBB")
    register_skills(str(tmp_path))
    assert expand_skill_command("/a then /b") == "AAA then BBB"

def test_expand_leaves_unknow_and_paths(tmp_path):
    register_skills(str(tmp_path))
    assert expand_skill_command("/unknown fix this") == "/unknown fix this"
    assert expand_skill_command("cat /tmp/x.txt") == "cat /tmp/x.txt"

def test_expand_keeps_backslashes(tmp_path):
    write_skill(tmp_path, "win", "---\nname: win\n---\nC:\\path\\d")
    register_skills(str(tmp_path))
    assert expand_skill_command("/win") == "C:\\path\\d"

def test_skips_non_mapping_frontmatter(tmp_path):
    write_skill(tmp_path, "bad", "---\nname:bad\n---\nbody")
    register_skills(str(tmp_path))
    assert _REGISTRY == {}
