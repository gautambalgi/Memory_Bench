"""Small tools that do useful work without shell access or arbitrary code execution."""

import ast
import math
import operator
import re
from pathlib import Path

MAX_BYTES = 16_000
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def calculate(expression: str) -> dict:
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 80:
        raise ValueError("Use a shorter expression with at most 80 syntax nodes.")

    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 12:
                raise ValueError("Exponents must be between -12 and 12.")
            value = OPERATORS[type(node.op)](left, right)
        else:
            raise ValueError("Only numbers, parentheses, and arithmetic operators are allowed.")
        if isinstance(value, complex) or not math.isfinite(value) or abs(value) > 1e15:
            raise ValueError("Results must be finite real numbers with magnitude at most 1e15.")
        return value

    return {"value": evaluate(tree.body)}


class Workspace:
    """One flat, private directory per run. Writes always create a new file."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, path: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\.(txt|md|json|csv)", path):
            raise ValueError("Use a simple filename ending in .txt, .md, .json, or .csv.")
        candidate = self.root / path
        if candidate.is_symlink() or candidate.resolve().parent != self.root:
            raise ValueError("The file must stay inside this run's workspace.")
        return candidate

    def write_file(self, path: str, content: str) -> dict:
        target = self.path(path)
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_BYTES:
            raise ValueError("Files must be 16,000 bytes or smaller.")
        # Exclusive creation prevents accidental overwrites and follows no existing links.
        with target.open("xb") as handle:
            handle.write(encoded)
        return {"path": path, "bytes": len(encoded)}

    def read_file(self, path: str) -> dict:
        with self.path(path).open("rb") as handle:
            content = handle.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ValueError("This file is too large to read.")
        return {"path": path, "content": content.decode("utf-8")}

    def list_files(self) -> dict:
        return {
            "files": sorted(
                p.name for p in self.root.iterdir() if p.is_file() and not p.is_symlink()
            )[:100]
        }


def text_stats(text: str) -> dict:
    return {"characters": len(text), "words": len(text.split()), "lines": len(text.splitlines())}
