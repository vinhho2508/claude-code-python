from app.tools import run_tool

def test_read_missing_file_returns_error():
    assert run_tool("Read", '{"file_path": "/nope.txt"}').startswith("Error")

def test_write_then_read(tmp_path):
    f = tmp_path / "a.txt"
    run_tool("Write", f'{{"file_path": "{f}", "content": "hi"}}')
    assert run_tool("Read", f'{{"file_path": "{f}"}}') == "hi"

def test_unknown_tool():
    assert "unknown tool" in run_tool("Nope", "{}")