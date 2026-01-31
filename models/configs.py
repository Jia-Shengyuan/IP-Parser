from dataclasses import dataclass
from typing import List


@dataclass
class VariableConfig:
    name: str
    type: str
    read: bool = False
    write: bool = False


@dataclass
class FunctionConfig:
    function_name: str
    arguments: List[VariableConfig]
