import asyncio

import pytest
from jsonschema import ValidationError

from memorybench.tools.builtin import Workspace, calculate, text_stats
from memorybench.tools.registry import ToolRegistry


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("18 * 0.24 + 7 * 0.61", 8.59),
        ("-(2+3)*4", -20),
        ("2**3", 8),
        ("9//2", 4),
        ("9%2", 1),
        ("1 / 4", 0.25),
    ],
)
def test_calculate(expression, expected):
    assert calculate(expression)["value"] == pytest.approx(expected)


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "True + 1",
        "[1, 2]",
        "2**100000",
        "1/0",
        "1e309",
        "(-1)**0.5",
        "1e15*10",
        "+".join(["1"] * 90),
    ],
)
def test_unsafe_or_unbounded_arithmetic(expression):
    with pytest.raises((ValueError, ZeroDivisionError)):
        calculate(expression)


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "C:/outside.txt",
        "nested/file.txt",
        ".env",
        "file.py",
        "a..txt",
        "\\outside.txt",
        "file.txt:secret",
        "a/b.txt",
    ],
)
def test_paths_stay_in_workspace(tmp_path, path):
    workspace = Workspace(tmp_path / "run")
    with pytest.raises(ValueError):
        workspace.write_file(path, "test")
    assert not list(workspace.root.iterdir())


def test_write_read_list_and_no_overwrite(tmp_path):
    workspace = Workspace(tmp_path)
    assert workspace.write_file("note.txt", "hello")["bytes"] == 5
    assert workspace.read_file("note.txt")["content"] == "hello"
    assert workspace.list_files() == {"files": ["note.txt"]}
    with pytest.raises(FileExistsError):
        workspace.write_file("note.txt", "changed")
    assert workspace.read_file("note.txt")["content"] == "hello"


def test_byte_limit_applies_to_unicode(tmp_path):
    with pytest.raises(ValueError):
        Workspace(tmp_path).write_file("big.txt", "🙂" * 5000)


def test_oversized_reads_are_rejected(tmp_path):
    (tmp_path / "large.txt").write_bytes(b"a" * 16001)
    with pytest.raises(ValueError):
        Workspace(tmp_path).read_file("large.txt")


def test_symlinks_are_rejected(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("private")
    workspace = Workspace(tmp_path / "run")
    try:
        (workspace.root / "link.txt").symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks requires privileges on this host.")
    with pytest.raises(ValueError):
        workspace.read_file("link.txt")


def test_stats():
    assert text_stats("Good memory\nstarts here.") == {
        "characters": 24,
        "words": 4,
        "lines": 2,
    }


@pytest.mark.parametrize(
    "name,arguments,exception",
    [
        ("unknown", "{}", ValueError),
        ("calculate", '{"expression": 5}', ValidationError),
        ("calculate", '{"expression": "2+2", "extra": 1}', ValidationError),
        ("calculate", "{}", ValidationError),
        ("calculate", "[]", ValidationError),
        ("calculate", "not json", ValueError),
    ],
)
def test_registry_validates(tmp_path, name, arguments, exception):
    with pytest.raises(exception):
        asyncio.run(ToolRegistry(Workspace(tmp_path)).execute(name, arguments, 1))


def test_tool_timeout_is_reported(tmp_path):
    import time

    from memorybench.tools.registry import Tool

    registry = ToolRegistry(Workspace(tmp_path))
    registry.tools["slow"] = Tool("slow", "Slow test operation", {}, lambda: time.sleep(0.05))
    with pytest.raises(TimeoutError):
        asyncio.run(registry.execute("slow", "{}", 0.001))
