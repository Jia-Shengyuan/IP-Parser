import sys
import os
from typing import List, Dict, Any
import json

# Allow importing from models directory by adding parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from clang.cindex import Index, CursorKind, TypeKind

from models.variables import Variable, VARIABLE_DOMAIN, VARIABLE_KIND
from models.functions import Function
from models.configs import FunctionConfig, VariableConfig
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
        self.config_function_names: set[str] = set()

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

        self._load_function_configs()

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

    def _load_function_configs(self) -> None:
        for filename, data in self._iter_function_config_files():
            self._parse_function_config_file(filename, data)

    def _iter_function_config_files(self) -> List[tuple[str, list]]:
        base_dir = self.project_path
        if os.path.isfile(base_dir):
            base_dir = os.path.dirname(base_dir)
        candidates = [
            os.path.join(base_dir, "config"),
            os.path.join(os.path.dirname(base_dir), "config"),
        ]
        items: List[tuple[str, list]] = []
        seen_paths = set()
        for config_dir in candidates:
            if not os.path.isdir(config_dir):
                continue
            for filename in os.listdir(config_dir):
                if not filename.endswith(".json"):
                    continue
                path = os.path.join(config_dir, filename)
                if path in seen_paths:
                    continue
                seen_paths.add(path)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue
                if not isinstance(data, list):
                    continue
                items.append((filename, data))
        return items

    def _parse_function_config_file(self, filename: str, data: list) -> None:
        def pointer_level(type_name: str) -> int:
            t = self.structs.get_decoded_name(type_name).strip()
            return t.count("*")

        def parse_ptr_target_name(target: Any) -> str | None:
            if target is None:
                return None
            if not isinstance(target, str):
                target = str(target)
            name = target.strip()
            if not name:
                return None
            if name.upper() in {"NULL", "nullptr".upper()}:
                return None
            return name

        for item in data:
            if not isinstance(item, dict):
                continue
            func_name = item.get("function_name")
            args = item.get("arguments", [])
            if not func_name or not isinstance(args, list):
                continue
            if any(f.name == func_name for f in self.functions):
                continue
            var_cfgs: List[VariableConfig] = []
            arg_type_map: Dict[str, str] = {}
            for arg in args:
                if not isinstance(arg, dict):
                    continue
                name = arg.get("name")
                type_str = arg.get("type")
                if not name or not type_str:
                    continue
                arg_type_map[name] = type_str
                var_cfgs.append(VariableConfig(
                    name=name,
                    type=type_str,
                    read=bool(arg.get("read", False)),
                    write=bool(arg.get("write", False)),
                ))
            func_cfg = FunctionConfig(function_name=func_name, arguments=var_cfgs)

            params = [vc.name for vc in func_cfg.arguments]
            func_vars_dict: Dict[str, Variable] = {}
            reads = set()
            writes = set()
            ptr_init_names: List[tuple[str, str | None]] = []
            for vc in func_cfg.arguments:
                raw_type = vc.type
                kind = VARIABLE_KIND.BUILTIN
                if self.structs.is_pointer(raw_type):
                    kind = VARIABLE_KIND.POINTER
                elif self.structs.is_array(raw_type):
                    kind = VARIABLE_KIND.ARRAY
                elif self.structs.is_struct(raw_type):
                    kind = VARIABLE_KIND.RECORD
                is_pointer = self.structs.is_pointer(raw_type)
                prefixed_name = f"<{func_name}>{vc.name}"
                func_vars_dict[prefixed_name] = Variable(
                    name=prefixed_name,
                    raw_type=raw_type,
                    kind=kind,
                    domain=VARIABLE_DOMAIN.PARAM,
                    is_pointer=is_pointer,
                    points_to={},
                )
                if is_pointer:
                    if vc.read:
                        reads.add(f"<{func_name}>{vc.name}__pointee")
                    if vc.write:
                        writes.add(f"<{func_name}>{vc.name}__pointee")

            ptr_init_items = item.get("ptr_init", [])
            if isinstance(ptr_init_items, list):
                for pi in ptr_init_items:
                    if not isinstance(pi, dict):
                        continue
                    src_name = pi.get("name")
                    tgt_name = parse_ptr_target_name(pi.get("target"))
                    if not src_name:
                        continue
                    src_prefixed = f"<{func_name}>{src_name}"
                    src_type = arg_type_map.get(src_name, "")
                    src_level = pointer_level(src_type) if src_type else 0
                    if src_level >= 2:
                        src_prefixed = f"{src_prefixed}__pointee"

                    tgt_prefixed: str | None = None
                    if tgt_name:
                        tgt_prefixed = f"<{func_name}>{tgt_name}"
                        tgt_type = arg_type_map.get(tgt_name, "")
                        tgt_level = pointer_level(tgt_type) if tgt_type else 0
                        if tgt_level >= 1:
                            tgt_prefixed = f"{tgt_prefixed}__pointee"
                    ptr_init_names.append((src_prefixed, tgt_prefixed))
            func = Function(
                name=func_name,
                source_file=os.path.join("config", filename),
                params=params,
                vars_dict=func_vars_dict,
                reads=reads,
                writes=writes,
                config_ptr_init_names=ptr_init_names,
            )
            self.functions.append(func)
            self._function_nodes.append((None, func))
            self.config_function_names.add(func_name)

