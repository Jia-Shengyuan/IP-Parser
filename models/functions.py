from models.variables import Variable
from typing import List, Dict, Set, Optional

class CallSite:
    """记录函数调用的信息"""
    def __init__(self, called_func: str, line: int):
        self.called_func = called_func  # 被调用的函数名
        self.line = line  # 调用所在的行号

class Function:

    def __init__(self, name: str, source_file: str, params: List[str] = [], vars_dict: Dict[str, Variable] = dict(),
                 reads: Set[str] = set(), writes: Set[str] = set(), calls: List[str] = list()):
        self.name = name
        self.source_file = source_file
        self.params = params
        self.vars_dict = vars_dict
        self.reads = reads
        self.writes = writes
        self.calls = calls  # 该函数调用的所有子函数名称列表

    