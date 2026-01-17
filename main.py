import json
import sys
import os

from parsing.parser import Parser
from memory_managing.memory import MemoryManager
from models.summarize import FunctionSummarize, BriefVariable


def _to_brief(var) -> BriefVariable:
	return BriefVariable(name=var.name, type=var.raw_type)


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
		r_any = len(var.read) > 0
		w_any = len(var.write) > 0

		# Only include variables that the target function reads or writes.
		if not (r_target or w_target):
			continue

		if r_any and not w_any:
			summary.interface_semantics.parameters.append(_to_brief(var))
		elif r_target and w_target and var.read.issubset({target_name}) and var.write.issubset({target_name}):
			summary.interface_semantics.state.append(_to_brief(var))
		elif r_target and not w_target:
			summary.interface_semantics.input.append(_to_brief(var))
		elif w_target and not r_target:
			summary.interface_semantics.output.append(_to_brief(var))
		else:
			summary.interface_semantics.inout.append(_to_brief(var))

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
		raise SystemExit("Usage: python main.py <function_name> [project_path]")

	function_name = sys.argv[1]
	project_path = sys.argv[2] if len(sys.argv) > 2 else "input"

	parser = Parser(project_path)
	parser.parse()

	summary = _summarize_function(parser, function_name)
	output_dir = "output"
	os.makedirs(output_dir, exist_ok=True)
	output_path = os.path.join(output_dir, f"results_{function_name}.json")
	with open(output_path, "w", encoding="utf-8") as f:
		f.write(json.dumps(_summary_to_dict(summary), ensure_ascii=False, indent=2))
	print(f"Summary for function '{function_name}' written to {output_path}")
