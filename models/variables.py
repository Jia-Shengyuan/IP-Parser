from enum import Enum
from typing import Dict

class VARIABLE_DOMAIN(Enum):
    GLOBAL = "Global"
    PARAM = "Param"
    LOCAL = "Local"
    RETURN = "Return"

class VARIABLE_KIND(Enum):
    POINTER = "Pointer"
    RECORD = "Record"
    ARRAY = "Array"
    BUILTIN = "Builtin"

class Variable:
    def __init__(self, name: str, raw_type: str, kind: VARIABLE_KIND, domain: VARIABLE_DOMAIN,
                 is_pointer: bool, points_to: Dict[str, int] = dict()):
        self.name = name
        self.raw_type = raw_type # The type given by clang
        self.kind = kind         # Type kind, such as `Pointer`, `Record`, `Array`, `Builtin` etc.
        self.domain = domain
        self.is_pointer = is_pointer
        self.points_to = points_to #pt: sub-variable name -> virtual memory location
        self.address = (-1, -1)    # (address, depth) in abstract memory model