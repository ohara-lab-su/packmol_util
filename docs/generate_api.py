#!/usr/bin/env python3
"""packmol_util の Python ソースから Jekyll 用 API Markdown を生成する。"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = Path(__file__).resolve().parent
MODULES = ["builder", "model", "packmol", "packmol_inp", "config", "param"]


def source_path(name: str) -> Path:
    candidates = [ROOT / "packmol_util" / f"{name}.py", ROOT / "src" / "packmol_util" / f"{name}.py"]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"packmol_util/{name}.py が見つかりません")


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = ast.unparse(node.args)
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{prefix} {node.name}({args}){returns}"


def emit_doc(lines: list[str], doc: str | None) -> None:
    if doc:
        lines.extend([doc.strip(), ""])


def main() -> None:
    out = [
        "---",
        "layout: page",
        "title: API リファレンス",
        "permalink: /api.html",
        "---",
        "",
        "# API リファレンス",
        "",
        "このページは `doc/generate_api.py` により Python ソースのシグネチャと docstring から自動生成されます。",
        "",
        "* TOC",
        "{:toc}",
        "",
    ]
    for name in MODULES:
        path = source_path(name)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        out.extend([f"## `packmol_util.{name}`", ""])
        emit_doc(out, ast.get_docstring(tree))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                out.extend([f"### `class {node.name}`", ""])
                emit_doc(out, ast.get_docstring(node))
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if child.name.startswith("_") and child.name != "__init__":
                            continue
                        out.extend([f"#### `{node.name}.{child.name}`", "", "```python", signature(child), "```", ""])
                        emit_doc(out, ast.get_docstring(child))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                out.extend([f"### `{node.name}`", "", "```python", signature(node), "```", ""])
                emit_doc(out, ast.get_docstring(node))
        out.append("---")
        out.append("")
    (DOC / "api.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
