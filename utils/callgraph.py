from __future__ import annotations

import os
from typing import Dict, Iterable, List, Set

from clang.cindex import Index, CursorKind


def build_call_graph(project_path: str) -> Dict[str, Set[str]]:
    """
    Parse a project and build a call graph (caller -> set of callees).
    Only includes functions defined within the project path.
    """
    project_path = os.path.abspath(project_path)
    index = Index.create()
    call_graph: Dict[str, Set[str]] = {}

    def iter_source_files() -> List[str]:
        if os.path.isfile(project_path):
            return [project_path]
        sources: List[str] = []
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith((".c", ".h")):
                    sources.append(os.path.join(root, file))
        return sources

    def is_in_project(cursor) -> bool:
        loc = cursor.location
        if not loc or not loc.file:
            return False
        return os.path.abspath(loc.file.name).startswith(project_path)

    def collect_calls(func_cursor, func_name: str) -> None:
        for child in func_cursor.get_children():
            if child.kind == CursorKind.CALL_EXPR:
                callee_name = child.spelling or ""
                if not callee_name:
                    ref = getattr(child, "referenced", None)
                    callee_name = getattr(ref, "spelling", "") if ref else ""
                if callee_name:
                    call_graph.setdefault(func_name, set()).add(callee_name)
            collect_calls(child, func_name)

    args = [f"-I{project_path}"]
    for file_path in iter_source_files():
        tu = index.parse(file_path, args=args)
        for cursor in tu.cursor.get_children():
            if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
                if not is_in_project(cursor):
                    continue
                func_name = cursor.spelling
                if not func_name:
                    continue
                call_graph.setdefault(func_name, set())
                collect_calls(cursor, func_name)

    return call_graph


def reverse_topo_from_root(call_graph: Dict[str, Iterable[str]], root: str) -> List[str]:
    """
    Return a reverse topological order starting from root.
    A function appears after all its callees.
    Unreachable functions are excluded.
    Assumes no recursion/cycles.
    """
    visited: Set[str] = set()
    order: List[str] = []

    stack: List[tuple[str, bool]] = [(root, False)]
    while stack:
        fn, expanded = stack.pop()
        if fn in visited and not expanded:
            continue
        if expanded:
            if fn not in visited:
                visited.add(fn)
            order.append(fn)
            continue
        if fn in visited:
            continue
        stack.append((fn, True))
        for callee in call_graph.get(fn, []):
            if callee not in visited:
                stack.append((callee, False))

    return order


def reverse_topo_from_project(project_path: str, root: str) -> List[str]:
    """
    Parse project and return reverse topological order from root.
    """
    graph = build_call_graph(project_path)
    return reverse_topo_from_root(graph, root)


__all__ = ["build_call_graph", "reverse_topo_from_root", "reverse_topo_from_project"]
