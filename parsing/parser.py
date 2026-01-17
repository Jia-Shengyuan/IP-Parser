import sys
import os
from typing import List, Dict, Optional, Tuple

# Allow importing from models directory by adding parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from clang.cindex import Index, CursorKind, TypeKind

from models.variables import Variable, VARIABLE_DOMAIN, VARIABLE_KIND
from models.functions import Function
from models.structs import StructsManager
from memory_managing.memory import MemoryManager

class Parser:

    def __init__(self, project_path: str):
        # Initialize parser state and caches.
        self.project_path = os.path.abspath(project_path)
        self.global_vars: List[Variable] = []
        self.functions: List[Function] = []
        self.structs = StructsManager.instance()
        self._seen_var_names = set() # Set of variable names for global deduplication
        self._seen_func_keys = set() # Set of (file_path, name) for function deduplication
        self._seen_struct_nodes = set() # Set of (file_path, line, col) for struct deduplication
        self._function_nodes = []  # List of (Cursor, Function)

    def parse(self):
        """
        Parse all source files in the project_path.
        """
        # Orchestrate parsing, memory allocation, and function analysis.
        index = Index.create()
        source_files = self._get_source_files()
        
        # Basic include arguments: include the project root
        args = [f'-I{self.project_path}']

        for file_path in source_files:
            # Parse the translation unit
            translation_unit = index.parse(file_path, args=args)
            self._visit_root(translation_unit.cursor)

        # Calculate struct sizes after all structs collected
        self.structs.calculate_size()

        memMana = MemoryManager.instance()
        memMana.allocate_globals(self.global_vars)

        for func_node, func in self._function_nodes:
            self.parse_function(func_node, func)

        memMana.analyze_memories()

    def _get_source_files(self) -> List[str]:
        """Recursive search for .c and .h files"""
        # Collect source file paths from project root or single file.
        if os.path.isfile(self.project_path):
            return [self.project_path]
            
        sources = []
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith((".c", ".h")):
                    sources.append(os.path.join(root, file))
        return sources

    def _visit_root(self, cursor):
        # Walk top-level declarations and dispatch handlers.
        for child in cursor.get_children():
            # Filter matches only from the current file (optional, but good for skipping system headers)
            # However, sometimes we might want to see what's in the included user headers.
            # For now, let's extract everything that is defined in the files we parse.
            
            if child.kind == CursorKind.VAR_DECL:
                self._extract_global_variable(child)
            elif child.kind == CursorKind.FUNCTION_DECL:
                self._extract_function(child)
            elif child.kind == CursorKind.STRUCT_DECL or child.kind == CursorKind.TYPEDEF_DECL:
                self._extract_struct(child)

    def _extract_struct(self, node):
        # Record struct definitions found in the project.
        location = node.location
        if not location.file:
            return
        file_path = os.path.abspath(location.file.name)
        if not file_path.startswith(self.project_path):
            return

        key = (file_path, location.line, location.column)
        if key in self._seen_struct_nodes:
            return
        self._seen_struct_nodes.add(key)

        self.structs.add_struct_from_node(node)

    def _extract_global_variable(self, node):
        # Extract and register global variable declarations.
        # 1. Project path check
        location = node.location
        if not location.file:
            return
        file_path = os.path.abspath(location.file.name)
        if not file_path.startswith(self.project_path):
            return

        # 2. Name extraction and Deduplication (Global by Name as per user request)
        name = node.spelling
        if not name:
            return
            
        if name in self._seen_var_names:
            return
        
        # 3. Note: We do NOT check is_definition() here, treating all declarations as potential globals
        # assuming code style ensures no name collisions for different variables.
        self._seen_var_names.add(name)

        type_obj = node.type
        raw_type = type_obj.spelling
        
        # Use canonical type to determine the underlying structure (e.g. resolve typedefs)
        canonical_type = type_obj.get_canonical()
        
        # Determine Kind based on clang TypeKind
        kind = VARIABLE_KIND.BUILTIN
        if canonical_type.kind == TypeKind.POINTER:
            kind = VARIABLE_KIND.POINTER
        elif canonical_type.kind == TypeKind.RECORD:
            kind = VARIABLE_KIND.RECORD
        elif canonical_type.kind in [TypeKind.CONSTANTARRAY, TypeKind.INCOMPLETEARRAY, TypeKind.VARIABLEARRAY, TypeKind.DEPENDENTSIZEDARRAY]:
            kind = VARIABLE_KIND.ARRAY
        
        is_pointer = (canonical_type.kind == TypeKind.POINTER)

        var = Variable(
            name=name,
            raw_type=raw_type,
            kind=kind,
            domain=VARIABLE_DOMAIN.GLOBAL,
            is_pointer=is_pointer,
            points_to={}
        )
        self.global_vars.append(var)

    def _extract_function(self, node):
        # Extract function definition metadata and store node for later analysis.
        # 1. Definition check (keep skipping prototypes for functions)
        if not node.is_definition():
            return

        # 2. Project path check
        location = node.location
        if not location.file:
            return
        file_path = os.path.abspath(location.file.name)
        if not file_path.startswith(self.project_path):
            return

        name = node.spelling
        if not name:
            return

        # 3. Deduplication (File path + Name)
        unique_key = (file_path, name)
        if unique_key in self._seen_func_keys:
            return
            
        self._seen_func_keys.add(unique_key)
        
        source_file = os.path.relpath(file_path, self.project_path)

        # Only parsing basic info for now as requested
        func = Function(
            name=name,
            source_file=source_file
        )
        self.functions.append(func)
        self._function_nodes.append((node, func))

    def parse_function(self, node, func: Function) -> None:
        """
        Parse a function node in sequential order and update Variable read/write sets.
        """
        # Sequentially walk the AST and mark read/write on global variables.
        mem = MemoryManager.instance()
        written: Dict[str, bool] = {}

        def mark_read(addr: int) -> None:
            # Record a read for the variable at this address.
            block = mem.get_block(addr)
            if block is None or block.var is None or block.var.is_pointer:
                return
            name = block.var.name
            if not written.get(name, False):
                mem.read_memory(addr, func.name)
                func.reads.add(name)

        def mark_write(addr: int) -> None:
            # Record a write for the variable at this address.
            block = mem.get_block(addr)
            if block is None or block.var is None or block.var.is_pointer:
                return
            name = block.var.name
            mem.write_memory(addr, func.name)
            func.writes.add(name)
            written[name] = True

        def handle_access(name: str, nonconst_index: bool, read: bool, write: bool, read_before_write: bool = False) -> None:
            # Resolve variable name to address and mark read/write once.
            if not name:
                return
            base_addr = mem.get_address(name)
            if base_addr is None:
                return

            addr = base_addr
            if read and read_before_write:
                mark_read(addr)
            if read and not read_before_write:
                mark_read(addr)
            if write:
                mark_write(addr)

        def get_integer_literal(cursor) -> Optional[str]:
            # Try to extract a constant integer literal from a cursor.
            if cursor.kind == CursorKind.INTEGER_LITERAL:
                tokens = [t.spelling for t in cursor.get_tokens()]
                return tokens[0] if tokens else None
            tokens = [t.spelling for t in cursor.get_tokens()]
            if tokens and tokens[0].isdigit():
                return tokens[0]
            return None

        def resolve_var_access(cursor) -> Tuple[Optional[str], bool]:
            # Resolve an access expression to a variable name and non-constant index flag.
            unwrap_kinds = (
                CursorKind.UNEXPOSED_EXPR,
                CursorKind.PAREN_EXPR,
                CursorKind.CSTYLE_CAST_EXPR,
            )
            if cursor.kind in unwrap_kinds:
                child = next(cursor.get_children(), None)
                return resolve_var_access(child) if child is not None else (None, False)
            if cursor.kind == CursorKind.DECL_REF_EXPR:
                return cursor.spelling, False
            if cursor.kind == CursorKind.MEMBER_REF_EXPR:
                children = list(cursor.get_children())
                if not children:
                    return None, False
                base_name, nonconst = resolve_var_access(children[0])
                if not base_name:
                    return None, False
                return f"{base_name}.{cursor.spelling}", nonconst
            if cursor.kind == CursorKind.ARRAY_SUBSCRIPT_EXPR:
                children = list(cursor.get_children())
                if len(children) < 2:
                    return None, False
                base_name, _ = resolve_var_access(children[0])
                if not base_name:
                    return None, False
                index_val = get_integer_literal(children[1])
                if index_val is None:
                    return base_name, True
                return f"{base_name}[{index_val}]", False
            return None, False

        def get_operator(cursor) -> str:
            # Detect the operator token for a given cursor.
            tokens = [t.spelling for t in cursor.get_tokens()]
            for op in ["+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=", "|=", "^=", "==", "=", "++", "--"]:
                if op in tokens:
                    return op
            return ""

        def handle_lvalue(cursor, is_compound: bool) -> None:
            # Handle lvalue writes, including compound assignments.
            name, nonconst = resolve_var_access(cursor)
            if name is None:
                return
            if is_compound:
                handle_access(name, nonconst, read=True, write=True, read_before_write=True)
            else:
                handle_access(name, nonconst, read=False, write=True)

        def handle_expr(cursor) -> None:
            # Walk expression nodes and apply read/write rules.
            if cursor.kind == CursorKind.CALL_EXPR:
                return
            if cursor.kind in (CursorKind.DECL_REF_EXPR, CursorKind.MEMBER_REF_EXPR, CursorKind.ARRAY_SUBSCRIPT_EXPR):
                name, nonconst = resolve_var_access(cursor)
                if name is not None:
                    handle_access(name, nonconst, read=True, write=False)
                return

            if cursor.kind == CursorKind.UNARY_OPERATOR:
                op = get_operator(cursor)
                child = next(cursor.get_children(), None)
                if child is None:
                    return
                if op in ("++", "--"):
                    handle_lvalue(child, is_compound=True)
                    return
                handle_expr(child)
                return

            if cursor.kind in (CursorKind.BINARY_OPERATOR, CursorKind.COMPOUND_ASSIGNMENT_OPERATOR):
                op = get_operator(cursor)
                children = list(cursor.get_children())
                if len(children) >= 2:
                    lhs, rhs = children[0], children[1]
                    if op == "=":
                        handle_lvalue(lhs, is_compound=False)
                        handle_expr(rhs)
                        return
                    if op in ("+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=", "|=", "^="):
                        handle_lvalue(lhs, is_compound=True)
                        handle_expr(rhs)
                        return
                    handle_expr(lhs)
                    handle_expr(rhs)
                    return

            for child in ordered_children(cursor):
                handle_expr(child)

        def ordered_children(cursor):
            # Return children in source order by location.
            children = list(cursor.get_children())
            def key(c):
                loc = c.location
                if loc and loc.line is not None and loc.column is not None:
                    return (loc.line, loc.column)
                return (0, 0)
            children.sort(key=key)
            return children

        for child in ordered_children(node):
            # Traverse function body in source order.
            handle_expr(child)
