from typing import List

'''
In summarize.py, we define classes used for outputing the summarized information.
Class FuncitionSummarize is what we want to output after summarization.
'''

class BriefVariable:
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type

class VariableSummarize:
    def __init__(self):
        self.parameters : List[BriefVariable] = []
        self.state : List[BriefVariable] = []
        self.input : List[BriefVariable] = []
        self.output : List[BriefVariable] = []
        self.inout : List[BriefVariable] = []

class FunctionSummarize:
    def __init__(self, function_name: str):
        self.function_name = function_name
        self.interface_semantics = VariableSummarize()
    