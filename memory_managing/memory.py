"""
This module handles the allocation for abstract memory location.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Iterable, Tuple, Any, Dict


@dataclass(frozen=True)
class Address:
	"""
	Abstract address represented by (start, depth).
	"""
	start: int
	depth: int


@dataclass
class MemoryBlock:
	"""
	Represents one abstract memory cell.
	"""
	addr: Address
	parent: Address
	pointers: List[Any] = field(default_factory=list)  # Variables pointing to this block


class MemoryManager:
	"""
	Abstract memory allocator.

	Address space starts from 1.
	Each allocation returns one or more consecutive blocks.
	"""

	def __init__(self) -> None:
		self._next_addr: int = 1
		self._blocks: List[List[MemoryBlock]] = [[]]  # index 0 unused

	def _ensure_capacity(self, max_addr: int) -> None:
		while len(self._blocks) <= max_addr:
			self._blocks.append([])

	def _alloc_blocks(self, count: int, parent: Address, depth: int) -> List[Address]:
		if count <= 0:
			raise ValueError("count must be positive")

		start_addr = self._next_addr
		end_addr = self._next_addr + count - 1
		self._ensure_capacity(end_addr)

		addrs = []
		for addr in range(start_addr, end_addr + 1):
			address = Address(start=addr, depth=depth)
			self._blocks[addr].append(MemoryBlock(addr=address, parent=parent))
			addrs.append(address)

		self._next_addr += count
		return addrs

	def allocate_scalar(self, var: Any, parent: Optional[Address] = None) -> Address:
		"""
		Allocate one block for a basic type.
		"""
		parent_addr = parent or Address(0, 0)
		depth = parent_addr.depth + 1 if parent_addr.start != 0 else 0
		addr = self._alloc_blocks(1, parent=parent_addr, depth=depth)[0]
		return addr

	def allocate_array(self, base_var: Any, length: int, parent: Optional[Address] = None) -> Tuple[Address, List[Address]]:
		"""
		Allocate blocks for an array of given length.
		Returns (base_addr, element_addrs).
		"""
		parent_addr = parent or Address(0, 0)
		base_depth = parent_addr.depth + 1 if parent_addr.start != 0 else 0
		base_addr = self._alloc_blocks(1, parent=parent_addr, depth=base_depth)[0]
		element_depth = base_depth + 1
		element_addrs = self._alloc_blocks(length, parent=base_addr, depth=element_depth)
		return base_addr, element_addrs

	def allocate_struct(self, base_var: Any, members: List[Tuple[Any, int]], parent: Optional[Address] = None) -> Dict[Any, Address]:
		"""
		Allocate blocks for a struct.
		Members: [(member_var, size_in_blocks), ...]
		Returns a mapping {member_var: start_addr}.
		"""
		parent_addr = parent or Address(0, 0)
		base_depth = parent_addr.depth + 1 if parent_addr.start != 0 else 0
		base_addr = self._alloc_blocks(1, parent=parent_addr, depth=base_depth)[0]
		member_depth = base_depth + 1

		member_start_map: Dict[Any, Address] = {}
		for member_var, size in members:
			if size <= 0:
				raise ValueError("member size must be positive")

			member_addrs = self._alloc_blocks(size, parent=base_addr, depth=member_depth)
			member_start_map[member_var] = member_addrs[0]

		return member_start_map

	def add_pointer(self, addr: Address, var: Any) -> None:
		"""
		Register a pointer variable to an address.
		"""
		block = self.get_block(addr)
		if not block:
			raise KeyError(f"Address {addr} not allocated")
		if var not in block.pointers:
			block.pointers.append(var)

	def remove_pointer(self, addr: Address, var: Any) -> None:
		block = self.get_block(addr)
		if not block:
			return
		if var in block.pointers:
			block.pointers.remove(var)

	def get_block(self, addr: Address) -> Optional[MemoryBlock]:
		if addr.start <= 0 or addr.start >= len(self._blocks):
			return None
		for block in self._blocks[addr.start]:
			if block.addr.depth == addr.depth:
				return block
		return None

	def iter_blocks(self) -> Iterable[MemoryBlock]:
		for bucket in self._blocks:
			for block in bucket:
				yield block

	def reset(self) -> None:
		self._next_addr = 1
		self._blocks = [[]]

