from enum import Enum
from typing import Dict, List

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
                 is_pointer: bool, address: int = 0, points_to: Dict[str, int] = dict()):
        self.name = name
        self.raw_type = raw_type # The type given by clang
        self.kind = kind         # Type kind, such as `Pointer`, `Record`, `Array`, `Builtin` etc.
        self.domain = domain
        self.is_pointer = is_pointer
        self.points_to = points_to #pt: sub-variable name -> virtual memory location
        self.address = address

        self.read = set()  # functions that read this variable before rewriting
        self.write = set() # functions that write to this variable

    def mark_read(self, function_name: str):
        if function_name not in self.read and function_name not in self.write:
            self.read.add(function_name)

    def mark_write(self, function_name: str):
        if function_name not in self.write:
            self.write.add(function_name)

# class VariablesManager:

#     def __init__(self):
#         self._variables: Dict[str, Variable] = dict()

#     def SetVariables(self, variables: List[Variable]):
#         for var in variables:
#             self._variables[var.name] = var
    
#     def GetVariable(self, name: str) -> Variable | None:
#         return self._variables.get(name, None)