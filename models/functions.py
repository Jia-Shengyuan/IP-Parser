from models.variables import Variable
from typing import List, Dict, Set

class Function:

    def __init__(self, name: str, source_file: str, params: List[str] = [], vars_dict: Dict[str, Variable] = dict(),
                 reads: Set[str] = set(), writes: Set[str] = set(), calls: Set[str] = set(), non_state: Set[str] = set()):
        
        self.name = name
        self.source_file = source_file
        self.params = params
        self.vars_dict = vars_dict
        self.reads = reads
        self.writes = writes
        self.calls = calls
        self.non_state = non_state

    