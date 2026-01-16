from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Iterable, Any, Optional

from clang.cindex import CursorKind

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


BUILTIN_TYPES = set ([
    "void", "char", "signed char", "unsigned char",
    "short", "unsigned short", "signed short", 
    "int", "signed", "signed int", "unsigned int",
    "long", "unsigned long", "signed long", 
    "long long", "unsigned long long", "signed long long",
    "float", "double", "long double", "_Bool", "bool",
    "size_t", "ptrdiff_t"])

_structs: Dict[str, Struct] = {}
_typeDict: Dict[str, str] = {} # typedef alias -> real type
_typeSize: Dict[str, int] = {}
_vis: Set[str] = set()

def _NormalizeTypeName(type_name: str) -> str:
    """
    Normalize type name by removing extra spaces.
    E.g., " unsigned   long  " -> "unsigned long"
    """
    return ' '.join(type_name.strip().split())

# here we guarantee that `curType` is a clean type name, which means no *, no [].
# the basic level of structs are `struct StructName`.
def _CalcTypeSize(curType: str):

    """
    For builtin types and pointer types, size = 1.
    For array types, size = element_size * length (simple "T[n]" form).
    We break up the type for the previous two cases, until only one clean type remains.

    For typedef, we resolve the alias first.
    For struct types, size = sum(member sizes).
    """

    curType = _NormalizeTypeName(curType)

    if curType.endswith("*") or curType in BUILTIN_TYPES:
        return 1
    
    if curType.endswith("]") and "[" in curType:

        base = curType[: curType.rfind("[")].strip()
        length_str = curType[curType.rfind("[") + 1 : -1].strip()

        # memo: will there be types like int a[], instead of int a[NUMBER]?
        length = int(length_str) if length_str.isdigit() else 1

        return _CalcTypeSize(base) * length
    
    if curType.startswith('(') and curType.endswith(')'):
        return _CalcTypeSize(curType[1:-1])
    
    assert curType.find('*') == -1 and curType.find('[') == -1 and curType.find('(') == -1, f"Type {curType} is not clean."
    
    # is an alias by typedef
    if curType in _typeDict:
        size = _CalcTypeSize(_typeDict[curType])
        _vis.add(curType)
        _typeSize[curType] = size
        return size

    # there should be no re-entry for the same struct type, since it's a DAG
    if curType in _vis:
        return _typeSize[curType]
    _vis.add(curType)

    struct = _structs.get(curType)
    if struct is None:
        raise TypeError(f"Undefined type {_structs} found when calculating size.")
    
    struct.size = 0
    for memberType in struct.member_types:
        struct.size += _CalcTypeSize(memberType)

    _typeSize[curType] = struct.size
    return struct.size


class StructsManager:
    """
    Manages struct definitions and computes sizes in topological order.

    Size rules (abstract memory):
    - builtin types: size = 1
    - pointer types: size = 1
    - array types: size = element_size * length (simple "T[n]" form)
    - struct types: size = sum(member sizes)
    """

    _instance: Optional["StructsManager"] = None

    def __new__(cls) -> "StructsManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._structs = _structs
        self._typeDict = _typeDict
        self._sizes: Dict[str, int] = {}

    @classmethod
    def instance(cls) -> "StructsManager":
        return cls()

    # what: input a struct definition from libclang node
    def add_struct_from_node(self, node: Any) -> Optional[Struct]:
        """
        Add a struct directly from a libclang node.
        The node can be a STRUCT_DECL cursor or a TYPEDEF_DECL cursor
        like: typedef struct { ... } A;
        """
        if node.kind == CursorKind.TYPEDEF_DECL:
            typedef_name = getattr(node, "spelling", "") or ""
            struct_node = self._get_struct_decl_from_typedef(node)
            if not struct_node or struct_node.kind != CursorKind.STRUCT_DECL:
                # Pure typedef (no struct definition here): only record alias.
                underlying = getattr(node, "underlying_typedef_type", None)
                underlying_name = getattr(underlying, "spelling", "") if underlying else ""
                if typedef_name and underlying_name:
                    self._typeDict[self._normalize_type_name(typedef_name)] = self._normalize_type_name(underlying_name)
                return None

        struct_node, name = self._resolve_struct_node_and_name(node)
        member_types = self._extract_member_types_from_node(struct_node)
        struct_def = Struct(name=name, member_types=member_types, node=struct_node)
        _structs[name] = struct_def
        return struct_def

    def get_struct(self, name: str) -> Struct | None:
        return _structs.get(name)
    
    def calculate_size(self):
        """
        Calculate sizes for all structs in topological order.
        This should be called once after all structs are added,
        and before the first usage of the size of Structs.
        """
        for struct_name in _structs.keys():
            if struct_name not in _vis:
                _CalcTypeSize(struct_name)
    
    def get_size(self, type_name: str) -> int:
        return _CalcTypeSize(type_name)

    def _extract_struct_name(self, node: Any) -> str:
        name = getattr(node, "spelling", "") or ""
        if name:
            return f"struct {name}"
        type_obj = getattr(node, "type", None)
        type_name = getattr(type_obj, "spelling", "") if type_obj else ""
        if type_name:
            t = self._normalize_type_name(type_name)
            return t if t.startswith("struct ") else f"struct {t}"
        node_id = getattr(node, "hash", None) or id(node)
        return f"__anon_struct_{node_id}"

    def _resolve_struct_node_and_name(self, node: Any) -> tuple[Any, str]:

        is_typedef = (node.kind == CursorKind.TYPEDEF_DECL)

        if is_typedef:
            typedef_name = getattr(node, "spelling", "") or ""
            struct_node = self._get_struct_decl_from_typedef(node) or node
            struct_name = self._extract_struct_name(struct_node)
            if typedef_name and not struct_name.startswith("__anon_struct_"):
                self._typeDict[self._normalize_type_name(typedef_name)] = struct_name
            return struct_node, struct_name

        return node, self._extract_struct_name(node)

    def _get_struct_decl_from_typedef(self, node: Any) -> Optional[Any]:
        type_obj = getattr(node, "underlying_typedef_type", None)
        if not type_obj:
            return None
        try:
            canonical = type_obj.get_canonical()
            return canonical.get_declaration()
        except Exception:
            return None

    def _extract_member_types_from_node(self, node: Any) -> List[str]:

        member_types: List[str] = []
        for child in getattr(node, "get_children", lambda: [])():
            if child.kind != CursorKind.FIELD_DECL:
                continue

            type_obj = getattr(child, "type", None)
            type_name = getattr(type_obj, "spelling", "") if type_obj else ""
            if not type_name:
                continue
            member_types.append(self._resolve_alias(type_name))

        return member_types

    def _resolve_alias(self, type_name: str) -> str:
        t = self._normalize_type_name(type_name)

        # Preserve pointer suffixes
        pointer_suffix = ""
        while t.endswith("*"):
            t = t[:-1].strip()
            pointer_suffix += "*"

        # Preserve array suffixes like "[10]" (outermost only)
        array_suffix = ""
        if t.endswith("]") and "[" in t:
            base = t[: t.rfind("[")].strip()
            array_suffix = t[t.rfind("["):]
            t = base

        seen = set()
        while t in self._typeDict and t not in seen:
            seen.add(t)
            t = self._typeDict[t]

        # If alias expands to something with array, keep it as is and append pointer suffix
        t = self._normalize_type_name(t)
        if array_suffix:
            t = f"{t}{array_suffix}"

        return f"{t}{pointer_suffix}"

    def _normalize_type_name(self, type_name: str) -> str:
        return " ".join(type_name.strip().split())
