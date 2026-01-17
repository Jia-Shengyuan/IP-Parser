import os
import sys

# Allow importing from models directory by adding parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from parsing.parser import Parser
from memory_managing.memory import MemoryManager

if __name__ == "__main__":

    if len(sys.argv) > 1:

        parser = Parser(sys.argv[1])
        parser.parse()
        memMana = MemoryManager.instance()

        print(f"Parsed {len(parser.global_vars)} global variables")

        for v in parser.global_vars:
            print(f"  G: {v.name}: {v.raw_type}, addr={v.address}, size={parser.structs.get_size(v.raw_type)}")
        print(f"Parsed {len(parser.functions)} functions")

        for f in parser.functions:
            print(f"  F: {f.name} in {f.source_file}")
        print(f"Parsed {len(parser.structs._structs)} structs")

        for s in parser.structs._structs.values():
            print(f"  S: {s.name} (size={s.size})")

        # print(f"  T: Integer (size={parser.structs.get_size('Integer')})")  # Example usage for pure typedef
        # print(f"  T: Array5 (size={parser.structs.get_size('Array5')})")

        print("\nMemory Blocks:")

        for addr, block in enumerate(memMana._blocks):
            if addr == 0:
                continue  # Skip address 0 which is unused
            print(f"  M: Addr {addr}: {block.var.name} (type {block.var.raw_type}, parent={block.parent}, size={parser.structs.get_size(block.var.raw_type)})")

        # 输出调用图
        print("\nCall Graph:")
        call_graph = parser.get_call_graph_dict()
        for caller, callees in call_graph.items():
            if callees:
                print(f"  {caller} -> {', '.join(callees)}")
            else:
                print(f"  {caller} -> (none)")

        # 输出逆拓扑排序
        print("\nReverse Topological Order (leaf functions first):")
        topo_order = parser.get_topological_order()
        for i, func_name in enumerate(topo_order):
            print(f"  {i+1}. {func_name}")