from typing import Dict, Optional, Tuple, Any

from clang.cindex import CursorKind, TypeKind

from models.functions import Function
from models.variables import Variable
from memory_managing.memory import MemoryManager


class FuncParser:

	UNWRAP_KINDS = (
		CursorKind.UNEXPOSED_EXPR,
		CursorKind.PAREN_EXPR,
		CursorKind.CSTYLE_CAST_EXPR,
	)

	_instance: Optional["FuncParser"] = None

	def __new__(cls) -> "FuncParser":
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance._initialized = False
		return cls._instance

	def __init__(self) -> None:
		if getattr(self, "_initialized", False):
			return
		self._initialized = True
		self._mem = MemoryManager.instance()
		self._pointer_map: Dict[str, Optional[int]] = {}
		self._global_pointer_inits: Dict[str, Any] = {}
		self._functions: Dict[str, tuple[Any, Function]] = {}

	@classmethod
	def instance(cls) -> "FuncParser":
		return cls._instance if cls._instance is not None else cls()

	def initialize(self, global_vars: list[Variable], global_pointer_inits: Dict[str, Any], function_nodes: list[tuple[Any, Function]]) -> None:
		# Initialize pointer map for global pointers and apply global initializers.
		self._pointer_map = {}
		self._global_pointer_inits = global_pointer_inits
		self._functions = {func.name: (node, func) for node, func in function_nodes}
		for var in global_vars:
			if var.is_pointer:
				self._pointer_map[var.name] = None

		for pointer_name, init_cursor in self._global_pointer_inits.items():
			target_addr = self._resolve_pointer_target_expr(init_cursor)
			if target_addr is not None:
				self._pointer_map[pointer_name] = target_addr
				self._mem.add_pointer_ref(target_addr, pointer_name)

	def finalize(self) -> None:
		# Aggregate child read/write information to parents.
		self._mem.analyze_memories()

	def _get_integer_literal_expr(self, cursor) -> Optional[str]:
		# Extract a constant integer literal from a cursor if present.
		if cursor is None:
			return None
		if cursor.kind == CursorKind.INTEGER_LITERAL:
			tokens = [t.spelling for t in cursor.get_tokens()]
			return tokens[0] if tokens else None
		tokens = [t.spelling for t in cursor.get_tokens()]
		if tokens and tokens[0].isdigit():
			return tokens[0]
		return None

	def _resolve_var_access_expr(self, cursor) -> Optional[str]:
		# Resolve a variable access expression to a fully-qualified name.
		if cursor is None:
			return None
		if cursor.kind in self.UNWRAP_KINDS:
			child = next(cursor.get_children(), None)
			return self._resolve_var_access_expr(child)
		if cursor.kind == CursorKind.DECL_REF_EXPR:
			return cursor.spelling
		if cursor.kind == CursorKind.MEMBER_REF_EXPR:
			children = list(cursor.get_children())
			if not children:
				return None
			base_name = self._resolve_var_access_expr(children[0])
			if not base_name:
				return None
			return f"{base_name}.{cursor.spelling}"
		if cursor.kind == CursorKind.ARRAY_SUBSCRIPT_EXPR:
			children = list(cursor.get_children())
			if len(children) < 2:
				return None
			base_name = self._resolve_var_access_expr(children[0])
			if not base_name:
				return None
			index_val = self._get_integer_literal_expr(children[1])
			if index_val is None:
				return base_name
			return f"{base_name}[{index_val}]"
		return None

	def _resolve_pointer_target_expr(self, expr) -> Optional[int]:
		# Resolve pointer initializer/assignment expression to a concrete address.
		if expr is None:
			return None
		if expr.kind in self.UNWRAP_KINDS:
			child = next(expr.get_children(), None)
			return self._resolve_pointer_target_expr(child)
		if expr.kind == CursorKind.UNARY_OPERATOR:
			tokens = [t.spelling for t in expr.get_tokens()]
			if "&" in tokens:
				child = next(expr.get_children(), None)
				name = self._resolve_var_access_expr(child)
				return self._mem.get_address(name) if name else None
		if expr.kind == CursorKind.DECL_REF_EXPR:
			pointer_name = expr.spelling
			return self._pointer_map.get(pointer_name)
		return None

	def parse_function(self, node, func: Function) -> None:
		"""
		Parse a function node in sequential order and update Variable read/write sets.
		"""
		self._mem.clear_pointer_refs()
		for pointer_name, init_cursor in self._global_pointer_inits.items():
			target_addr = self._resolve_pointer_target_expr(init_cursor)
			if target_addr is not None:
				self._mem.add_pointer_ref(target_addr, pointer_name)

		written: Dict[str, bool] = {}
		pointer_map: Dict[str, Optional[int]] = dict(self._pointer_map)
		call_stack = set()
		self._parse_function_with_context(node, func, func, pointer_map, written, call_stack)

	def _parse_function_with_context(
		self,
		node,
		current_func: Function,
		root_func: Function,
		pointer_map: Dict[str, Optional[int]],
		written: Dict[str, bool],
		call_stack: set[str]
	) -> None:
		# Parse with shared pointer map and root function attribution.
		if current_func.name in call_stack:
			return
		call_stack.add(current_func.name)
		func_prefix = f"<{current_func.name}>"

		def resolve_pointer_key(name: Optional[str]) -> Optional[str]:
			# Prefer function-local pointer name if present, otherwise global name.
			if not name:
				return None
			local_key = f"{func_prefix}{name}"
			if local_key in pointer_map:
				return local_key
			return name if name in pointer_map else None

		def mark_read(addr: int) -> None:
			# Record a read for the variable at this address.
			block = self._mem.get_block(addr)
			if block is None or block.var is None or block.var.is_pointer:
				return
			name = block.var.name
			if not written.get(name, False):
				self._mem.read_memory(addr, root_func.name)
				root_func.reads.add(name)

		def mark_write(addr: int) -> None:
			# Record a write for the variable at this address.
			block = self._mem.get_block(addr)
			if block is None or block.var is None or block.var.is_pointer:
				return
			name = block.var.name
			self._mem.write_memory(addr, root_func.name)
			root_func.writes.add(name)
			written[name] = True

		def handle_access(name: str, nonconst_index: bool, read: bool, write: bool, read_before_write: bool = False) -> None:
			# Resolve variable name to address and mark read/write once.
			if not name:
				return
			base_addr = self._mem.get_address(name)
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
			if cursor.kind in FuncParser.UNWRAP_KINDS:
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
				ptr_key = resolve_pointer_key(base_name)
				if ptr_key:
					target_addr = pointer_map.get(ptr_key)
					if target_addr is not None:
						block = self._mem.get_block(target_addr)
						if block is not None and block.var is not None:
							base_name = block.var.name
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

		def resolve_pointer_name(cursor) -> Optional[str]:
			# Resolve a pointer variable name from an expression.
			if cursor is None:
				return None
			if cursor.kind in FuncParser.UNWRAP_KINDS:
				child = next(cursor.get_children(), None)
				return resolve_pointer_name(child)
			if cursor.kind == CursorKind.DECL_REF_EXPR:
				return cursor.spelling
			return None

		def update_pointer_mapping(pointer_name: str, target_addr: Optional[int]) -> None:
			# Update pointer mapping and memory back-references.
			old_addr = pointer_map.get(pointer_name)
			if old_addr is not None:
				self._mem.remove_pointer_ref(old_addr, pointer_name)
			pointer_map[pointer_name] = target_addr
			if target_addr is not None:
				self._mem.add_pointer_ref(target_addr, pointer_name)

		def get_operator(cursor) -> str:
			# Detect the operator token for a given cursor.
			tokens = [t.spelling for t in cursor.get_tokens()]
			for op in [
				"+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=", "|=", "^=",
				"==", "=", "++", "--", "*", "&"
			]:
				if op in tokens:
					return op
			return ""

		def resolve_pointer_target(expr) -> Optional[int]:
			# Resolve a pointer initializer/assignment target to an address.
			if expr is None:
				return None
			if expr.kind in FuncParser.UNWRAP_KINDS:
				child = next(expr.get_children(), None)
				return resolve_pointer_target(child)
			if expr.kind == CursorKind.UNARY_OPERATOR and get_operator(expr) == "&":
				child = next(expr.get_children(), None)
				if child is None:
					return None
				name, _ = resolve_var_access(child)
				return self._mem.get_address(name) if name else None
			ptr_name = resolve_pointer_name(expr)
			ptr_key = resolve_pointer_key(ptr_name)
			if ptr_key is not None:
				return pointer_map.get(ptr_key)
			return None

		def handle_lvalue(cursor, is_compound: bool) -> None:
			# Handle lvalue writes, including compound assignments.
			if cursor.kind in FuncParser.UNWRAP_KINDS:
				child = next(cursor.get_children(), None)
				if child is not None:
					handle_lvalue(child, is_compound)
				return
			if cursor.kind == CursorKind.UNARY_OPERATOR and get_operator(cursor) == "*":
				child = next(cursor.get_children(), None)
				ptr_name = resolve_pointer_name(child)
				ptr_key = resolve_pointer_key(ptr_name)
				if ptr_key:
					target_addr = pointer_map.get(ptr_key)
					if target_addr is not None:
						if is_compound:
							mark_read(target_addr)
						mark_write(target_addr)
				return
			name, nonconst = resolve_var_access(cursor)
			if name is None:
				return
			if resolve_pointer_key(name):
				# Pointer assignment should not count as read/write on pointer itself.
				return
			if is_compound:
				handle_access(name, nonconst, read=True, write=True, read_before_write=True)
			else:
				handle_access(name, nonconst, read=False, write=True)

		def handle_expr(cursor) -> None:
			
			# Walk expression nodes and apply read/write rules.
			if cursor.kind == CursorKind.VAR_DECL:
				# Track local pointer declarations and initializers.
				var_name = cursor.spelling
				if var_name and cursor.type.kind == TypeKind.POINTER:
					local_key = f"{func_prefix}{var_name}"
					pointer_map[local_key] = None
					init_child = next(cursor.get_children(), None)
					if init_child is not None:
						target_addr = resolve_pointer_target(init_child)
						update_pointer_mapping(local_key, target_addr)
						handle_expr(init_child)
					return
				init_child = next(cursor.get_children(), None)
				if init_child is not None:
					handle_expr(init_child)
				return
			
			if cursor.kind == CursorKind.CALL_EXPR:
				
				# Mark global non-pointer arguments (any occurrence) as reads.
				def collect_arg_reads(expr) -> None:
					if expr is None:
						return
					if expr.kind in FuncParser.UNWRAP_KINDS:
						child = next(expr.get_children(), None)
						collect_arg_reads(child)
						return
					if expr.kind == CursorKind.UNARY_OPERATOR and get_operator(expr) == "*":
						child = next(expr.get_children(), None)
						ptr_name = resolve_pointer_name(child)
						ptr_key = resolve_pointer_key(ptr_name)
						if ptr_key:
							target_addr = pointer_map.get(ptr_key)
							if target_addr is not None:
								mark_read(target_addr)
						return
					name, _ = resolve_var_access(expr)
					if name:
						addr = self._mem.get_address(name)
						if addr is not None:
							block = self._mem.get_block(addr)
							if block is not None and block.var is not None and not block.var.is_pointer:
								mark_read(addr)
							# Avoid double-counting base identifiers in subscript/member expressions.
							if expr.kind in (CursorKind.ARRAY_SUBSCRIPT_EXPR, CursorKind.MEMBER_REF_EXPR):
								return
					for child in ordered_children(expr):
						collect_arg_reads(child)

				for arg in cursor.get_arguments():
					collect_arg_reads(arg)

				callee_name = cursor.spelling or ""
				if not callee_name:
					referenced = getattr(cursor, "referenced", None)
					callee_name = getattr(referenced, "spelling", "") if referenced else ""

				if callee_name and callee_name in self._functions:
					callee_node, callee_func = self._functions[callee_name]
					param_names = callee_func.params or []
					arg_nodes = list(cursor.get_arguments())
					updated_keys: Dict[str, Optional[int]] = {}

					for i, param_name in enumerate(param_names):
						if i >= len(arg_nodes):
							break
						target_addr = resolve_pointer_target(arg_nodes[i])
						param_key = f"<{callee_func.name}>{param_name}"
						updated_keys[param_key] = pointer_map.get(param_key)
						update_pointer_mapping(param_key, target_addr)

					self._parse_function_with_context(
						callee_node,
						callee_func,
						root_func,
						pointer_map,
						written,
						call_stack
					)

					for key, old_addr in updated_keys.items():
						update_pointer_mapping(key, old_addr)

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
				if op == "*":
					ptr_name = resolve_pointer_name(child)
					ptr_key = resolve_pointer_key(ptr_name)
					if ptr_key:
						target_addr = pointer_map.get(ptr_key)
						if target_addr is not None:
							mark_read(target_addr)
					return
				if op == "&":
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
						lhs_name, _ = resolve_var_access(lhs)
						lhs_key = resolve_pointer_key(lhs_name)
						if lhs_key:
							# Pointer assignment: update mapping without read/write on pointer.
							target_addr = resolve_pointer_target(rhs)
							update_pointer_mapping(lhs_key, target_addr)
							handle_expr(rhs)
							return
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

		call_stack.remove(current_func.name)
