from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Iterable, Any, Optional


@dataclass
class Struct:
    """
    Represents a struct type.

    member_types: list of member type names (order preserved).
    """
    name: str
    member_types: List[str] = field(default_factory=list)
    size: int = 0
    node: Optional[Any] = None


class StructsManager:
    """
    Manages struct definitions and computes sizes in topological order.

    Size rules (abstract memory):
    - builtin types: size = 1
    - pointer types: size = 1
    - array types: size = element_size * length (simple "T[n]" form)
    - struct types: size = sum(member sizes)
    """

    def __init__(self) -> None:
        self._structs: Dict[str, Struct] = {}
        self._builtin_sizes: Dict[str, int] = {}
        self._sizes: Dict[str, int] = {}

    def add_struct(self, struct_def: Struct) -> None:
        self._structs[struct_def.name] = struct_def

    def add_struct_from_node(self, node: Any) -> Struct:
        """
        Add a struct directly from a libclang node.
        The node is expected to be a STRUCT_DECL cursor.
        """
        name = self._extract_struct_name(node)
        member_types = self._extract_member_types_from_node(node)
        struct_def = Struct(name=name, member_types=member_types, node=node)
        self._structs[name] = struct_def
        return struct_def

    def get_struct(self, name: str) -> Struct | None:
        return self._structs.get(name)

    def set_builtin_size(self, type_name: str, size: int = 1) -> None:
        self._builtin_sizes[type_name] = size

    def compute_sizes(self) -> Dict[str, int]:
        """
        Compute sizes for all structs in topological order.
        """
        self._sizes.clear()
        for struct_name in self._topo_order():
            size = self._compute_struct_size(struct_name)
            self._sizes[struct_name] = size
            self._structs[struct_name].size = size
        return dict(self._sizes)

    def get_size(self, type_name: str) -> int:
        """
        Get size for any type name (builtin / pointer / array / struct).
        """
        type_name = type_name.strip()

        # Pointer types
        if type_name.endswith("*"):
            return 1

        # Array types: "T[n]"
        if type_name.endswith("]") and "[" in type_name:
            base, length = self._split_array_type(type_name)
            return self.get_size(base) * length

        # Builtin types
        if type_name in self._builtin_sizes:
            return self._builtin_sizes[type_name]

        # Struct types
        if type_name in self._structs:
            if type_name not in self._sizes:
                self._sizes[type_name] = self._compute_struct_size(type_name)
            return self._sizes[type_name]

        # Fallback
        return 1

    def _compute_struct_size(self, struct_name: str) -> int:
        struct_def = self._structs[struct_name]
        return sum(self.get_size(t) for t in struct_def.member_types)

    def _extract_struct_name(self, node: Any) -> str:
        name = getattr(node, "spelling", "") or ""
        if name:
            return name
        type_obj = getattr(node, "type", None)
        type_name = getattr(type_obj, "spelling", "") if type_obj else ""
        if type_name:
            return self._normalize_type_name(type_name)
        node_id = getattr(node, "hash", None) or id(node)
        return f"__anon_struct_{node_id}"

    def _extract_member_types_from_node(self, node: Any) -> List[str]:
        try:
            from clang.cindex import CursorKind
        except Exception:
            CursorKind = None

        member_types: List[str] = []
        for child in getattr(node, "get_children", lambda: [])():
            if CursorKind is None:
                kind_name = getattr(getattr(child, "kind", None), "name", None)
                if kind_name != "FIELD_DECL":
                    continue
            else:
                if child.kind != CursorKind.FIELD_DECL:
                    continue

            type_obj = getattr(child, "type", None)
            type_name = getattr(type_obj, "spelling", "") if type_obj else ""
            if not type_name:
                continue
            member_types.append(self._normalize_type_name(type_name))

        return member_types

    def _topo_order(self) -> List[str]:
        """
        Topological order of structs based on member type dependencies.
        """
        visited: Set[str] = set()
        temp: Set[str] = set()
        order: List[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in temp:
                raise ValueError(f"Cycle detected in struct definitions at {name}")

            temp.add(name)
            struct_def = self._structs[name]
            for t in struct_def.member_types:
                base_type = self._strip_array_and_pointer(t)
                if base_type in self._structs:
                    visit(base_type)
            temp.remove(name)
            visited.add(name)
            order.append(name)

        for name in self._structs.keys():
            visit(name)

        return order

    def _strip_array_and_pointer(self, type_name: str) -> str:
        t = type_name.strip()
        if t.endswith("*"):
            return t.rstrip("*").strip()
        if t.endswith("]") and "[" in t:
            base, _ = self._split_array_type(t)
            return base
        return t

    def _split_array_type(self, type_name: str) -> tuple[str, int]:
        base = type_name[: type_name.rfind("[")].strip()
        length_str = type_name[type_name.rfind("[") + 1 : -1].strip()
        length = int(length_str) if length_str.isdigit() else 1
        return self._normalize_type_name(base), length

    def _normalize_type_name(self, type_name: str) -> str:
        t = type_name.strip()
        if t.startswith("struct "):
            t = t[len("struct "):].strip()
        return t
