import sys
import os
from typing import List, Dict, Any

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
from parsing.func_parser import FuncParser
from utils.callgraph import reverse_topo_from_project

class Parser:

    def __init__(self, project_path: str):
        # Initialize parser state and caches.
        self.project_path = os.path.abspath(project_path)
        self.global_vars: List[Variable] = []
        self.functions: List[Function] = []
        self.structs = StructsManager.instance()
        self._global_var_map: Dict[str, Variable] = {}
        self._seen_var_names = set() # Set of variable names for global deduplication
        self._seen_func_keys = set() # Set of (file_path, name) for function deduplication
        self._seen_struct_nodes = set() # Set of (file_path, line, col) for struct deduplication
        self._function_nodes = []  # List of (Cursor, Function)
        self._global_pointer_inits: Dict[str, Any] = {}  # pointer var name -> init cursor

    def parse(self, entry_function: str | None = None):
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

        func_parser = FuncParser.instance()
        func_parser.initialize(self.global_vars, self._global_pointer_inits, self._function_nodes, {})

        if entry_function:
            order = reverse_topo_from_project(self.project_path, entry_function)
            func_map = {func.name: (node, func) for node, func in self._function_nodes}
            for func_name in order:
                if func_name in func_map:
                    func_node, func = func_map[func_name]
                    func_parser.parse_function(func_node, func)
        else:
            for func_node, func in self._function_nodes:
                func_parser.parse_function(func_node, func)

        func_parser.finalize()

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
            elif child.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL, CursorKind.TYPEDEF_DECL):
                self._extract_struct(child)
            elif child.kind == CursorKind.ENUM_DECL:
                self._extract_enum(child)

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

    def _extract_enum(self, node):
        # Record enum definitions found in the project.
        location = node.location
        if not location.file:
            return
        file_path = os.path.abspath(location.file.name)
        if not file_path.startswith(self.project_path):
            return

        self.structs.add_enum_from_node(node)

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
			
        if name in self._global_var_map:
            # Allow later definition/initializer (e.g. weak symbol in header).
            if node.type.get_canonical().kind == TypeKind.POINTER:
                init_child = next(node.get_children(), None)
                if init_child is not None:
                    self._global_pointer_inits[name] = init_child
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
        self._global_var_map[name] = var

        if is_pointer:
            init_child = next(node.get_children(), None)
            if init_child is not None:
                self._global_pointer_inits[name] = init_child

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
        params = []
        func_vars_dict: Dict[str, Variable] = {}
        for child in node.get_children():
            if child.kind == CursorKind.PARM_DECL:
                param_name = child.spelling
                if param_name:
                    params.append(param_name)
                    param_type = child.type
                    raw_type = param_type.spelling
                    canonical_type = param_type.get_canonical()
                    if canonical_type.kind == TypeKind.POINTER:
                        kind = VARIABLE_KIND.POINTER
                    elif canonical_type.kind == TypeKind.RECORD:
                        kind = VARIABLE_KIND.RECORD
                    elif canonical_type.kind in [TypeKind.CONSTANTARRAY, TypeKind.INCOMPLETEARRAY, TypeKind.VARIABLEARRAY, TypeKind.DEPENDENTSIZEDARRAY]:
                        kind = VARIABLE_KIND.ARRAY
                    else:
                        kind = VARIABLE_KIND.BUILTIN
                    is_pointer = (canonical_type.kind == TypeKind.POINTER)
                    prefixed_name = f"<{name}>{param_name}"
                    func_vars_dict[prefixed_name] = Variable(
                        name=prefixed_name,
                        raw_type=raw_type,
                        kind=kind,
                        domain=VARIABLE_DOMAIN.PARAM,
                        is_pointer=is_pointer,
                        points_to={}
                    )

        func = Function(
            name=name,
            source_file=source_file,
            params=params,
            vars_dict=func_vars_dict
        )
        self.functions.append(func)
        self._function_nodes.append((node, func))

