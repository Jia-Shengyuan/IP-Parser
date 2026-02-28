from models.variables import Variable
from typing import List, Dict, Set

class Function:

    def __init__(
        self,
        name: str,
        source_file: str,
        params: List[str] | None = None,
        vars_dict: Dict[str, Variable] | None = None,
        reads: Set[str] | None = None,
        writes: Set[str] | None = None,
        calls: Set[str] | None = None,
        non_state: Set[str] | None = None,
        ptr_init: Dict[int, int] | None = None,
        config_ptr_init_names: List[tuple[str, str]] | None = None,
    ):

        self.name = name
        self.source_file = source_file
        self.params = params or []
        self.vars_dict = vars_dict or {}
        self.reads = reads or set()
        self.writes = writes or set()
        self.calls = calls or set()
        self.non_state = non_state or set()
        self.ptr_init = ptr_init or {}
        self.config_ptr_init_names = config_ptr_init_names or []

    