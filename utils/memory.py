"""
This module handles the allocation for abstract memory location.
This module is incomplete.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable, Tuple, Any


@dataclass
class MemoryBlock:
	"""
	Represents one abstract memory cell.
	"""
	addr: int
	parent: int = 0
	pointers: List[Any] = field(default_factory=list)  # Variables pointing to this block
	owners: List[Any] = field(default_factory=list)    # Variables owning this block (from high to low)


class MemoryManager:
	"""
	Abstract memory allocator.

	Address space starts from 1.
	Each allocation returns one or more consecutive blocks.
	"""

	def __init__(self) -> None:
		self._next_addr: int = 1
		self._blocks: Dict[int, MemoryBlock] = {}

	def _alloc_blocks(self, count: int, parent: int = 0) -> List[int]:
		if count <= 0:
			raise ValueError("count must be positive")

		addrs = list(range(self._next_addr, self._next_addr + count))
		for addr in addrs:
			self._blocks[addr] = MemoryBlock(addr=addr, parent=parent)
		self._next_addr += count
		return addrs

	def allocate_scalar(self, var: Any, parent: int = 0) -> int:
		"""
		Allocate one block for a basic type.
		"""
		addr = self._alloc_blocks(1, parent=parent)[0]
		self.add_owner(addr, var)
		return addr

	def allocate_array(self, base_var: Any, length: int, parent: int = 0) -> Tuple[int, List[int]]:
		"""
		Allocate blocks for an array of given length.
		Returns (base_addr, element_addrs).
		"""
		element_addrs = self._alloc_blocks(length, parent=0)
		base_addr = element_addrs[0]

		# Set parent for each element to the array base
		for addr in element_addrs:
			self._blocks[addr].parent = base_addr
			self.add_owner(addr, base_var)

		# If this array itself is nested, link base block to parent
		if parent != 0:
			self._blocks[base_addr].parent = parent

		return base_addr, element_addrs

	def allocate_struct(self, base_var: Any, members: List[Tuple[Any, int]], parent: int = 0) -> Dict[Any, int]:
		"""
		Allocate blocks for a struct.
		Members: [(member_var, size_in_blocks), ...]
		Returns a mapping {member_var: start_addr}.
		"""
		total_size = sum(size for _, size in members)
		addrs = self._alloc_blocks(total_size, parent=0)
		base_addr = addrs[0]

		# Base owner for all blocks
		for addr in addrs:
			self._blocks[addr].parent = base_addr
			self.add_owner(addr, base_var)

		# If this struct itself is nested, link base block to parent
		if parent != 0:
			self._blocks[base_addr].parent = parent

		member_start_map: Dict[Any, int] = {}
		cursor = 0
		for member_var, size in members:
			if size <= 0:
				raise ValueError("member size must be positive")

			start_addr = addrs[cursor]
			member_start_map[member_var] = start_addr

			for i in range(size):
				addr = addrs[cursor + i]
				self.add_owner(addr, member_var)

			cursor += size

		return member_start_map

	def add_pointer(self, addr: int, var: Any) -> None:
		"""
		Register a pointer variable to an address.
		"""
		block = self._blocks.get(addr)
		if not block:
			raise KeyError(f"Address {addr} not allocated")
		if var not in block.pointers:
			block.pointers.append(var)

	def remove_pointer(self, addr: int, var: Any) -> None:
		block = self._blocks.get(addr)
		if not block:
			return
		if var in block.pointers:
			block.pointers.remove(var)

	def add_owner(self, addr: int, var: Any) -> None:
		"""
		Add an owner for an address. Owners are stored in hierarchical order
		(e.g. [a, a[0]] or [b, b.x]).
		"""
		block = self._blocks.get(addr)
		if not block:
			raise KeyError(f"Address {addr} not allocated")
		if var not in block.owners:
			block.owners.append(var)

	def get_block(self, addr: int) -> Optional[MemoryBlock]:
		return self._blocks.get(addr)

	def iter_blocks(self) -> Iterable[MemoryBlock]:
		return self._blocks.values()

	def reset(self) -> None:
		self._next_addr = 1
		self._blocks.clear()

