from app.skill import Skill, get_skills, format_skills_prompt

def write_skill(root, folder, content):
    d = root / folder
    d.mkdir()
    (d / "SKILL.md").write_text(content)

def test_missing_dir_returns_empty(tmp_path):
    assert get_skills(str(tmp_path / "nope")) == []

def test_reads_skills_sorted_and_skips_folders_without_skill_md(tmp_path):
    write_skill(tmp_path, "b", "---\nname: beta\ndescription: second\n---\nbody")
    write_skill(tmp_path, "a", "---\nname: alpha\ndescription: first\n---\nbody")
    (tmp_path / "empty").mkdir()
    assert get_skills(str(tmp_path)) == [Skill("alpha", "first"), Skill("beta", "second")]

def test_name_falls_back_to_folder(tmp_path):
    write_skill(tmp_path, "deploy", "---\ndescription: ship it\n---\n")
    assert get_skills(str(tmp_path)) == [Skill("deploy", "ship it")]

def test_skips_file_without_frontmatter(tmp_path):
    write_skill(tmp_path, "x", "just text")
    assert get_skills(str(tmp_path)) == []

def test_format_prompt():
    assert format_skills_prompt([]) == ""
    assert format_skills_prompt([Skill("a", "b")]).endswith("- a: b")
