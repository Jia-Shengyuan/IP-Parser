import json
import sys
import os

from parsing.parser import Parser
from memory_managing.memory import MemoryManager
from models.summarize import FunctionSummarize, BriefVariable
from utils.callgraph import reverse_topo_from_project


def _to_brief(var) -> BriefVariable:
	name = var.name
	if name.endswith("__pointee"):
		return None
	if name.startswith("<") and ">" in name:
		name = name.split(">", 1)[1]
	return BriefVariable(name=name, type=getattr(var, "original_raw_type", var.raw_type))


def _summarize_function(parser: Parser, target_name: str) -> FunctionSummarize:
	mem = MemoryManager.instance()

	target_func = None
	for func in parser.functions:
		if func.name == target_name:
			target_func = func
			break
	if target_func is None:
		raise ValueError(f"Function '{target_name}' not found")

	summary = FunctionSummarize(function_name=target_name)

	for block in mem._blocks:
		if block is None or block.parent != 0:
			continue
		var = block.var
		if var is None:
			continue

		r_target = target_name in var.read
		w_target = target_name in var.write

		# Only include variables that the target function reads or writes.
		if not (r_target or w_target):
			continue

		if r_target and not w_target and var.domain == var.domain.GLOBAL:
			brief = _to_brief(var)
			if brief:
				summary.interface_semantics.parameters.append(brief)
		elif (
			r_target and w_target
			and var.domain == var.domain.GLOBAL
			and var.read.issubset({target_name})
			and var.write.issubset({target_name})
			and var.name not in target_func.non_state
		):
			brief = _to_brief(var)
			if brief:
				summary.interface_semantics.state.append(brief)
		elif r_target and not w_target:
			brief = _to_brief(var)
			if brief:
				summary.interface_semantics.input.append(brief)
		elif w_target and not r_target:
			brief = _to_brief(var)
			if brief:
				summary.interface_semantics.output.append(brief)
		else:
			brief = _to_brief(var)
			if brief:
				summary.interface_semantics.inout.append(brief)

	return summary


def _summary_to_dict(summary: FunctionSummarize) -> dict:
	def serialize_vars(items):
		return [{"name": v.name, "type": v.type} for v in items]

	return {
		"function_name": summary.function_name,
		"interface_semantics": {
			"parameters": serialize_vars(summary.interface_semantics.parameters),
			"state": serialize_vars(summary.interface_semantics.state),
			"input": serialize_vars(summary.interface_semantics.input),
			"output": serialize_vars(summary.interface_semantics.output),
			"inout": serialize_vars(summary.interface_semantics.inout),
		},
	}


if __name__ == "__main__":
	if len(sys.argv) < 2:
		raise SystemExit("Usage: python main.py <function_name> [project_path] [output_dir] [--memory]")

	function_name = sys.argv[1]
	project_path = "input"
	output_dir = "output"
	if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
		project_path = sys.argv[2]
	if len(sys.argv) > 3 and not sys.argv[3].startswith("--"):
		output_dir = sys.argv[3]

	with_memory = any(arg == "--memory" for arg in sys.argv[2:])

	parser = Parser(project_path)
	parser.parse(entry_function=function_name)

	order = reversed(reverse_topo_from_project(project_path, function_name))
	func_names = [name for name in order if any(f.name == name for f in parser.functions)]
	if function_name not in func_names:
		func_names.append(function_name)

	summaries = [
		_summarize_function(parser, name)
		for name in func_names
		if name not in getattr(parser, "config_function_names", set())
	]
	os.makedirs(output_dir, exist_ok=True)
	output_path = os.path.join(output_dir, f"results_{function_name}.json")
	with open(output_path, "w", encoding="utf-8") as f:
		f.write(json.dumps([_summary_to_dict(s) for s in summaries], ensure_ascii=False, indent=2))
	print(f"Summaries for reachable functions from '{function_name}' written to {output_path}")

	if with_memory:
		mem = MemoryManager.instance()
		memory_path = os.path.join(output_dir, f"memory_{function_name}.txt")
		with open(memory_path, "w", encoding="utf-8") as f:
			f.write("Memory Blocks:\n\n")
			for addr, block in enumerate(mem._blocks):
				if addr == 0 or block is None:
					continue
				if getattr(block.var, "hidden", False):
					continue
				read_funcs = sorted(block.var.read)
				write_funcs = sorted(block.var.write)
				f.write(
					f"  M: Addr {addr}: {block.var.name} "
					f"(type {block.var.raw_type}, parent={block.parent}, size={parser.structs.get_size(block.var.raw_type)})\n"
				)
				f.write(f"     R: {', '.join(read_funcs) if read_funcs else '-'}\n")
				f.write(f"     W: {', '.join(write_funcs) if write_funcs else '-'}\n")
		print(f"Memory report for '{function_name}' written to {memory_path}")
