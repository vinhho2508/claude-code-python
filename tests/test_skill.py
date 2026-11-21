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

def test_expand_arguments_whole(tmp_path):
    write_skill(tmp_path, "apple", "---\nname: apple\n---\n$ARGUMENTS")
    register_skills(str(tmp_path))
    assert expand_skill_command("/apple 4127") == ["4127"]

def test_expand_positional_reversed(tmp_path):
    write_skill(tmp_path, "grape", "---\nname: grape\n---\n$1 $0")
    register_skills(str(tmp_path))
    assert expand_skill_command("/grape mango pear") == ["pear mango"]

def test_expand_indexed_and_multi_digit(tmp_path):
    write_skill(tmp_path, "x", "---\nname: x\n---\n$ARGUMENTS[1]|$10|$1")
    register_skills(str(tmp_path))
    assert expand_skill_command("/x " + " ".join("abcdefghijk")) == ["b|k|b"]

def test_expand_no_args_and_out_of_range_become_empty(tmp_path):
    write_skill(tmp_path, "x", "---\nname: x\n---\n[$ARGUMENTS][$0][$5]")
    register_skills(str(tmp_path))
    assert expand_skill_command("/x") == ["[][][]"]

def test_expand_does_not_resubstitute_inserted_args(tmp_path):
    write_skill(tmp_path, "x", "---\nname: x\n---\n$ARGUMENTS")
    register_skills(str(tmp_path))
    assert expand_skill_command("/x $0 y") == ["$0 y"]

def test_expand_appends_when_body_has_no_placeholder(tmp_path):
    write_skill(tmp_path, "review", "---\nname: review\n---\nREVIEW IT")
    register_skills(str(tmp_path))
    assert expand_skill_command("/review app.py") == ["REVIEW IT\n\nARGUMENTS: app.py"]

def test_expand_stacks_until_first_non_skill(tmp_path):
    write_skill(tmp_path, "a", "---\nname: a\n---\nA-$ARGUMENTS")
    write_skill(tmp_path, "b", "---\nname: b\n---\nB-$ARGUMENTS")
    register_skills(str(tmp_path))
    assert expand_skill_command("/a /b 4127") == ["A-4127", "B-4127"]
    assert expand_skill_command("/a 4127 /b") == ["A-4127 /b"]

def test_expand_leaves_unknown_and_paths(tmp_path):
    register_skills(str(tmp_path))
    assert expand_skill_command("/unknown fix this") == ["/unknown fix this"]
    assert expand_skill_command("cat /tmp/x.txt") == ["cat /tmp/x.txt"]

def test_expand_keeps_backslashes(tmp_path):
    write_skill(tmp_path, "win", "---\nname: win\n---\nC:\\path\\d")
    register_skills(str(tmp_path))
    assert expand_skill_command("/win") == ["C:\\path\\d"]

def test_skips_non_mapping_frontmatter(tmp_path):
    write_skill(tmp_path, "bad", "---\nname:bad\n---\nbody")
    register_skills(str(tmp_path))
    assert _REGISTRY == {}
