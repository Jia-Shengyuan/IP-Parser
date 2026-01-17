"""
This module handles the allocation for abstract memory location.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Iterable, Tuple, Any, Dict
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
	pointers: List[Any] = field(default_factory=list)  # Variables pointing to this block


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

	@classmethod
	def instance(cls) -> "MemoryManager":
		return cls._instance if cls._instance is not None else cls()

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
		self._blocks.append(MemoryBlock(addr = addr, parent=parent,
								    	var = variable if variable is not None else Variable(
			name = var_name,
			raw_type = type_name,
			kind = structs_manager.get_type_kind(type_name),
			domain = VARIABLE_DOMAIN.GLOBAL,
			is_pointer = structs_manager.is_pointer(type_name),
			address=addr
		)))
		self._next_addr += 1

		# case: basic type, including builtins and pointers -> finished
		if structs_manager.is_basic_type(type_name):
			return addr

		# case: array type
		if structs_manager.is_array(type_name):
			base_type, length = structs_manager.parse_array_type(type_name)
			for i in range(length):
				self._allocate(f"{var_name}[{i}]", base_type, parent=addr, structs_manager=structs_manager)
			return addr
		
		# case: struct type
		struct = structs_manager.get_struct(type_name)
		if struct is None and not type_name.startswith("struct "):
			struct = structs_manager.get_struct(f"struct {type_name}")

		if struct is not None:
			for (member_type, member_name) in zip(struct.member_types, struct.member_names):
				self._allocate(var_name + "." + member_name, member_type, parent=addr, structs_manager=structs_manager)
			return addr
		
		raise TypeError(f"Unknown type for allocation: {type_name}")