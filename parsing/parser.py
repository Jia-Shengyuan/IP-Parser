import sys
import os
from typing import List
from collections import deque

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

        self.project_path = os.path.abspath(project_path)
        self.global_vars: List[Variable] = []
        self.functions: List[Function] = []
        self.structs = StructsManager.instance()
        self._seen_var_names = set() # Set of variable names for global deduplication
        self._seen_func_keys = set() # Set of (file_path, name) for function deduplication
        self._seen_struct_nodes = set() # Set of (file_path, line, col) for struct deduplication
        self._cached_translation_units = {}  # 缓存已解析的 translation units，避免重复解析

    def parse(self):
        """
        Parse all source files in the project_path.
        """
        index = Index.create()
        source_files = self._get_source_files()

        # Basic include arguments: include the project root
        args = [f'-I{self.project_path}']

        for file_path in source_files:
            # Parse the translation unit and cache it
            translation_unit = index.parse(file_path, args=args)
            self._cached_translation_units[file_path] = translation_unit
            self._visit_root(translation_unit.cursor)

        # Calculate struct sizes after all structs collected
        self.structs.calculate_size()

        memMana = MemoryManager()
        memMana.allocate_globals(self.global_vars)

        # Build call graph using cached translation units
        self._build_call_graph()

    def _get_source_files(self) -> List[str]:
        """Recursive search for .c and .h files"""
        if os.path.isfile(self.project_path):
            return [self.project_path]
            
        sources = []
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith((".c", ".h")):
                    sources.append(os.path.join(root, file))
        return sources

    def _visit_root(self, cursor):
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

        # Extract parameters
        params = []
        for param in node.get_arguments():
            param_name = param.spelling
            if param_name:
                params.append(param_name)

        func = Function(
            name=name,
            source_file=source_file,
            params=params
        )
        self.functions.append(func)

    def _build_call_graph(self):
        """
        构建函数调用图，分析每个函数调用了哪些子函数
        使用缓存的 translation units，避免重复解析
        """
        # 先清空所有函数的 calls 列表
        for func in self.functions:
            func.calls = []

        # 创建函数名称到 Function 对象的映射
        func_dict = {func.name: func for func in self.functions}

        # 使用缓存的 translation units
        for file_path, translation_unit in self._cached_translation_units.items():
            self._visit_function_calls(translation_unit.cursor, func_dict, None)

    def _visit_function_calls(self, cursor, func_dict, current_func):
        """
        遍历 AST，提取函数调用关系
        current_func: 当前所在的函数对象
        """
        # 检查是否进入了一个新的函数
        if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
            func_name = cursor.spelling
            current_func = func_dict.get(func_name, None)

        # 只处理当前项目文件中的节点
        if cursor.location.file:
            file_path = os.path.abspath(cursor.location.file.name)
            if not file_path.startswith(self.project_path):
                for child in cursor.get_children():
                    self._visit_function_calls(child, func_dict, current_func)
                return

        if cursor.kind == CursorKind.CALL_EXPR:
            # 获取被调用函数的名称
            called_name = cursor.spelling

            # 记录调用关系：当前函数调用了 called_name
            if current_func and called_name and called_name in func_dict:
                if called_name not in current_func.calls:
                    current_func.calls.append(called_name)

        for child in cursor.get_children():
            self._visit_function_calls(child, func_dict, current_func)

    def get_topological_order(self):
        """
        获取函数的逆拓扑排序（从叶节点到根节点）
        用于自底向上的分析：先处理不调用其他函数的函数（叶子），再处理调用它们的函数

        返回顺序：叶子函数 -> 中间函数 -> 根函数
        """
        # 构建调用图：func_name -> [called_functions]
        call_graph = {func.name: func.calls[:] for func in self.functions}

        # 计算每个函数的出度（调用了多少个其他函数）
        # 出度为0的函数是叶子函数
        out_degree = {func.name: len(func.calls) for func in self.functions}

        # 反转调用图：called -> [callers]
        # 用于追踪：当某个函数的所有依赖（被调用的函数）都处理完后，该函数就可以处理了
        reverse_call_graph = {}
        for func_name in out_degree.keys():
            reverse_call_graph[func_name] = []

        for caller, callees in call_graph.items():
            for callee in callees:
                if callee in reverse_call_graph:
                    reverse_call_graph[callee].append(caller)

        # 初始队列：出度为0的函数（叶子函数）
        queue = deque([name for name, degree in out_degree.items() if degree == 0])

        topo_order = []
        while queue:
            func_name = queue.popleft()
            topo_order.append(func_name)

            # 这个函数处理完后，检查哪些函数可以开始处理
            # 即：这个函数是哪些函数的被调用者
            for caller in reverse_call_graph[func_name]:
                out_degree[caller] -= 1
                if out_degree[caller] == 0:
                    queue.append(caller)

        return topo_order

    def get_call_graph_dict(self):
        """
        返回调用图的字典表示，便于调试和输出
        """
        return {func.name: func.calls[:] for func in self.functions}
