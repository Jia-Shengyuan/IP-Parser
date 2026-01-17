"""
This module handles the allocation for abstract memory location.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Iterable, Tuple, Any, Dict, Set
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

	@classmethod
	def instance(cls) -> "MemoryManager":
		return cls._instance if cls._instance is not None else cls()
	
	def get_address(self, var_name: str) -> Optional[int]:
		"""
		Get the allocated address for a variable name.
		Returns None if not an global variable.
		"""
		return self._map.get(var_name, None)

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

	def remove_pointer_ref(self, target_addr: int, pointer_name: str) -> None:
		block = self.get_block(target_addr)
		if block is None:
			return
		block.pointers.discard(pointer_name)

	def clear_pointer_refs(self) -> None:
		for block in self.iter_blocks():
			block.pointers.clear()

	# what: should be called when a function reads a variable in the abstract memory
	def read_memory(self, addr: int, func: str):
		
		block = self._blocks[addr]

		if func in block.var.write:
			return  # already overwritten, no need to mark read
		
		# read to a memory is viewed as reading all the pointers pointing towards it
		for pointer in block.pointers:
			pointer_addr = self.get_address(pointer)
			if pointer_addr is not None:
				self._mark_read(pointer_addr, func)

		size = StructsManager.instance().get_size(block.var.raw_type)
		for i in range(size):
			self._mark_read(addr + i, func)

	# what: should be called when a function writes to a variable in the abstract memory
	def write_memory(self, addr: int, func: str):

		block = self._blocks[addr]

		for pointer in block.pointers:
			pointer_addr = self.get_address(pointer)
			if pointer_addr is not None:
				self._mark_write(pointer_addr, func)

		size = StructsManager.instance().get_size(block.var.raw_type)
		for i in range(size):
			self._mark_write(addr + i, func)

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
			base_type, length = structs_manager.parse_array_type(type_name)
			for i in range(length):
				variable.points_to[str(i)] = self._next_addr
				self._allocate(f"{var_name}[{i}]", base_type, parent=addr, structs_manager=structs_manager)
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