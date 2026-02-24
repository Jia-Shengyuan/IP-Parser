"""
This module handles the allocation for abstract memory location.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Iterable, Dict, Set
from models import *

@dataclass
class MemoryBlock:
	"""
	Represents one abstract memory cell.
	"""
	addr: int
	parent: int
	var: Variable
	ptr_value: Optional[int] = None  # If this block is a pointer, the address it points to
	pointers: Set[str] = field(default_factory=set)  # Pointer variable names pointing to this block


class MemoryManager:
	"""
	Abstract memory allocator.

	Address space starts from 1.
	Each allocation returns one or more consecutive blocks.
	"""

	_instance: Optional["MemoryManager"] = None
	ARRAY_UNKNOWN_INDEX = -1

	def __new__(cls) -> "MemoryManager":
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance._initialized = False
		return cls._instance

	def __init__(self) -> None:
		if getattr(self, "_initialized", False):
			return
		self._initialized = True
		self._next_addr: int = 1
		self._blocks: List[Optional[MemoryBlock]] = [None]  # index 0 unused
		self._map: Dict[str, int] = dict()  # var_name -> address
		self._dirty_ptr_blocks: Set[int] = set()

	@classmethod
	def instance(cls) -> "MemoryManager":
		return cls._instance if cls._instance is not None else cls()
	
	def get_address(self, var_name: str) -> Optional[int]:
		"""
		Get the allocated address for a variable name.
		Returns None if not an global variable.
		"""
		return self._map.get(var_name, None)

	def _array_index_to_text(self, index: int) -> str:
		return "?" if index == self.ARRAY_UNKNOWN_INDEX else str(index)

	def _ensure_array_child(self, parent_addr: int, parent_name: str, index: int) -> Optional[int]:
		parent_block = self.get_block(parent_addr)
		if parent_block is None or parent_block.var is None:
			return None
		parent_var = parent_block.var
		if parent_var.kind != VARIABLE_KIND.ARRAY:
			return None
		key = index
		child_addr = parent_var.points_to.get(key)
		if child_addr is not None:
			return child_addr
		structs_manager = StructsManager.instance()
		base_type, _ = structs_manager.parse_array_type(parent_var.raw_type)
		child_name = f"{parent_name}[{self._array_index_to_text(index)}]"
		existing_addr = self._map.get(child_name)
		if existing_addr is not None:
			parent_var.points_to[key] = existing_addr
			return existing_addr
		parent_var.points_to[key] = self._next_addr
		self._allocate(child_name, base_type, parent=parent_addr, structs_manager=structs_manager)
		return parent_var.points_to.get(key)

	def ensure_address(self, var_name: str) -> Optional[int]:
		if not var_name:
			return None
		addr = self._map.get(var_name)
		if addr is not None:
			return addr
		n = len(var_name)
		i = 0
		while i < n and var_name[i] not in ".[" and not (var_name[i] == "-" and i + 1 < n and var_name[i + 1] == ">"):
			i += 1
		if i == 0:
			return None
		root_name = var_name[:i]
		current_addr = self._map.get(root_name)
		if current_addr is None:
			return None
		while i < n:
			current_block = self.get_block(current_addr)
			if current_block is None or current_block.var is None:
				return None
			current_var = current_block.var
			if var_name[i] == "." or (var_name[i] == "-" and i + 1 < n and var_name[i + 1] == ">"):
				i += 2 if (var_name[i] == "-" and i + 1 < n and var_name[i + 1] == ">") else 1
				start = i
				while i < n and var_name[i] not in ".[" and not (var_name[i] == "-" and i + 1 < n and var_name[i + 1] == ">"):
					i += 1
				if i == start:
					return None
				member_name = var_name[start:i]
				child_addr = current_var.points_to.get(member_name)
				if child_addr is None:
					return None
				current_addr = child_addr
				continue
			if var_name[i] == "[":
				j = var_name.find("]", i)
				if j < 0:
					return None
				index_text = var_name[i + 1:j].strip()
				if index_text == "?":
					index_val = self.ARRAY_UNKNOWN_INDEX
				elif index_text.isdigit():
					index_val = int(index_text)
				else:
					return None
				child_addr = current_var.points_to.get(index_val)
				if child_addr is None:
					child_addr = self._ensure_array_child(current_addr, current_var.name, index_val)
				if child_addr is None:
					return None
				current_addr = child_addr
				i = j + 1
				continue
			return None
		return current_addr

	def get_block(self, addr: int) -> Optional[MemoryBlock]:
		if addr <= 0 or addr >= len(self._blocks):
			raise IndexError(f"Invalid memory address: {addr}, max address is {len(self._blocks)-1}")
		return self._blocks[addr]

	def iter_blocks(self) -> Iterable[MemoryBlock]:
		for block in self._blocks:
			if block is not None:
				yield block

	def _mark_read(self, addr: int, func: str):
		self._blocks[addr].var.mark_read(func)

	def _mark_write(self, addr: int, func: str):
		self._blocks[addr].var.mark_write(func)

	def add_pointer_ref(self, target_addr: int, pointer_name: str) -> None:
		block = self.get_block(target_addr)
		if block is None:
			return
		block.pointers.add(pointer_name)
		self._dirty_ptr_blocks.add(target_addr)

	def _iter_pointer_refs(self, addr: int) -> Set[str]:
		refs: Set[str] = set()
		current = addr
		while current and current < len(self._blocks):
			block = self._blocks[current]
			if block is None:
				break
			refs.update(block.pointers)
			current = block.parent
		return refs

	def remove_pointer_ref(self, target_addr: int, pointer_name: str) -> None:
		block = self.get_block(target_addr)
		if block is None:
			return
		block.pointers.discard(pointer_name)
		self._dirty_ptr_blocks.add(target_addr)

	def clear_pointer_refs(self) -> None:
		for addr in self._dirty_ptr_blocks:
			block = self.get_block(addr)
			if block is not None:
				block.pointers.clear()
		self._dirty_ptr_blocks.clear()

	# what: should be called when a function reads a variable in the abstract memory
	def read_memory(self, addr: int, func: str):
		
		block = self._blocks[addr]

		if func in block.var.write:
			return  # already overwritten, no need to mark read
		
		# read to a memory is viewed as reading all the pointers pointing towards it
		for pointer in self._iter_pointer_refs(addr):
			pointer_addr = self.get_address(pointer)
			if pointer_addr is not None:
				self._mark_read(pointer_addr, func)

		self._mark_read(addr, func)

	# what: should be called when a function writes to a variable in the abstract memory
	def write_memory(self, addr: int, func: str):

		block = self._blocks[addr]

		for pointer in self._iter_pointer_refs(addr):
			pointer_addr = self.get_address(pointer)
			if pointer_addr is not None:
				self._mark_write(pointer_addr, func)

		self._mark_write(addr, func)

	def analyze_memories(self):
		
		graph = [[] for _ in range(len(self._blocks))]

		def dfs(addr: int): # returns the read, write flag
			var = self._blocks[addr].var
			if graph[addr] == []: # leaf
				return (var.read, var.write)
			for child_addr in graph[addr]:
				child_read, child_write = dfs(child_addr)
				var.read = var.read.union(child_read)
				var.write = var.write.union(child_write)
			return (var.read, var.write)

		for addr, block in enumerate(self._blocks):
			if addr == 0:
				continue
			graph[block.parent].append(addr)

		for global_var_addr in graph[0]:
			dfs(global_var_addr)

	def allocate_globals(self, variables: List[Variable]):
		"""
		Allocate abstract memory for a list of global variables.
		Each variable's `address` field is updated with the allocated address.
		"""		
		structs_manager = StructsManager.instance()
		for var in variables:
			addr = self._allocate(var.name, var.raw_type, parent=0, structs_manager=structs_manager, variable=var)
			var.address = addr
			# self._blocks[addr].var = var  # Update with the original variable info

	def allocate_params(self, variables: List[Variable]) -> Dict[str, int]:
		"""
		Allocate abstract memory for a list of parameter variables.
		Returns a mapping of pointer param name -> dummy pointee address.
		"""
		structs_manager = StructsManager.instance()
		pointer_defaults: Dict[str, int] = {}
		for var in variables:
			addr = self._allocate(var.name, var.raw_type, parent=0, structs_manager=structs_manager, variable=var)
			var.address = addr
			if var.is_pointer:
				base_type = structs_manager.get_decoded_name(var.raw_type).rstrip()
				if base_type.endswith("*"):
					base_type = base_type[:-1].strip()
				if not base_type:
					base_type = "void"
				dummy_name = f"{var.name}__pointee"
				dummy_type = base_type
				if var.is_pointer_array:
					array_len = max(var.pointer_array_len, 1)
					dummy_type = f"{base_type}[{array_len}]"
				dummy_var = Variable(
					name=dummy_name,
					raw_type=dummy_type,
					kind=structs_manager.get_type_kind(dummy_type),
					domain=var.domain,
					is_pointer=False,
					points_to={},
				)
				dummy_addr = self._allocate(dummy_name, dummy_type, parent=0, structs_manager=structs_manager, variable=dummy_var)
				pointer_defaults[var.name] = dummy_addr
				self.add_pointer_ref(dummy_addr, var.name)
		return pointer_defaults

	def allocate_params_for_function(self, variables: List[Variable]) -> Dict[str, int]:
		"""
		Allocate abstract memory for a function's parameter variables.
		Pointer params with detected array usage are allocated as arrays.
		Returns a mapping of pointer param name -> dummy pointee address.
		"""
		structs_manager = StructsManager.instance()
		pointer_defaults: Dict[str, int] = {}
		for var in variables:
			if var.address:
				continue
			if var.is_pointer and var.is_pointer_array:
				base_type = structs_manager.get_decoded_name(var.raw_type).rstrip()
				if base_type.endswith("*"):
					base_type = base_type[:-1].strip()
				array_len = max(var.pointer_array_len, 1)
				array_type = f"{base_type}[{array_len}]"
				var.raw_type = array_type
				var.kind = VARIABLE_KIND.ARRAY
				var.is_pointer = False
			addr = self._allocate(var.name, var.raw_type, parent=0, structs_manager=structs_manager, variable=var)
			var.address = addr
			if var.is_pointer:
				base_type = structs_manager.get_decoded_name(var.raw_type).rstrip()
				if base_type.endswith("*"):
					base_type = base_type[:-1].strip()
				if not base_type:
					base_type = "void"
				dummy_name = f"{var.name}__pointee"
				dummy_type = base_type
				if var.is_pointer_array:
					array_len = max(var.pointer_array_len, 1)
					dummy_type = f"{base_type}[{array_len}]"
				dummy_var = Variable(
					name=dummy_name,
					raw_type=dummy_type,
					kind=structs_manager.get_type_kind(dummy_type),
					domain=var.domain,
					is_pointer=False,
					points_to={},
				)
				dummy_addr = self._allocate(dummy_name, dummy_type, parent=0, structs_manager=structs_manager, variable=dummy_var)
				pointer_defaults[var.name] = dummy_addr
				self.add_pointer_ref(dummy_addr, var.name)
		return pointer_defaults

	def ensure_pointer_array(self, dummy_name: str, base_type: str, length: int) -> None:
		if length <= 0:
			return
		addr = self.get_address(dummy_name)
		if addr is None:
			return
		block = self.get_block(addr)
		if block is None or block.var is None:
			return
		current_len = 0
		if block.var.kind == VARIABLE_KIND.ARRAY:
			try:
				_, current_len = StructsManager.instance().parse_array_type(block.var.raw_type)
			except Exception:
				current_len = 0
		if length > current_len:
			block.var.raw_type = f"{base_type}[{length}]"
			block.var.kind = VARIABLE_KIND.ARRAY
			block.var.is_pointer = False
			self._ensure_array_child(addr, dummy_name, self.ARRAY_UNKNOWN_INDEX)
			for i in range(length):
				self._ensure_array_child(addr, dummy_name, i)

	def convert_pointer_param_to_array(self, var_name: str, base_type: str, length: int) -> None:
		if length <= 0:
			return
		addr = self.get_address(var_name)
		if addr is None:
			return
		block = self.get_block(addr)
		if block is None or block.var is None:
			return
		block.var.raw_type = f"{base_type}[{length}]"
		block.var.kind = VARIABLE_KIND.ARRAY
		block.var.is_pointer = False
		self._ensure_array_child(addr, var_name, self.ARRAY_UNKNOWN_INDEX)
		for i in range(length):
			self._ensure_array_child(addr, var_name, i)

		dummy_name = f"{var_name}__pointee"
		for b in self._blocks:
			if b is None or b.var is None:
				continue
			if b.var.name == dummy_name or b.var.name.startswith(f"{dummy_name}[") or b.var.name.startswith(f"{dummy_name}."):
				b.var.hidden = True

	def _allocate(self, var_name: str, type_name: str, parent: int, structs_manager: StructsManager, variable: Variable | None = None) -> int:
		
		"""
		Allocate a variable by its type name, recursively allocating children.
		Always allocates one block for the variable itself, then handles array/struct.
		"""

		type_name = structs_manager.get_decoded_name(type_name)
		addr = self._next_addr

		if variable is None:
			variable = Variable(
				name = var_name,
				raw_type = type_name,
				kind = structs_manager.get_type_kind(type_name),
				domain = VARIABLE_DOMAIN.GLOBAL,
				is_pointer = structs_manager.is_pointer(type_name),
				address=addr
			)

		self._blocks.append(MemoryBlock(addr, parent, variable))

		self._map[var_name] = addr
		self._next_addr += 1

		# case: basic type, including builtins and pointers -> finished
		if structs_manager.is_basic_type(type_name):
			return addr

		# case: array type
		if structs_manager.is_array(type_name):
			self._ensure_array_child(addr, var_name, self.ARRAY_UNKNOWN_INDEX)
			return addr
		
		# case: struct type
		struct = structs_manager.get_struct(type_name)
		if struct is None and not type_name.startswith("struct "):
			struct = structs_manager.get_struct(f"struct {type_name}")

		if struct is not None:
			for (member_type, member_name) in zip(struct.member_types, struct.member_names):
				variable.points_to[member_name] = self._next_addr
				self._allocate(var_name + "." + member_name, member_type, parent=addr, structs_manager=structs_manager)
			return addr
		
		raise TypeError(f"Unknown type for allocation: {type_name}")