from typing import List, Dict, Set, Optional
from core.variable import Variable


class FunctionUnit:
    """
    表示一个函数：局部分析 + 传播分析
    """

    def __init__(self, name: str, api: str = None):
        self.name: str = name
        self.api: str = api

        self.params: List[Variable] = []       # 形参
        self.locals: Dict[str, Variable] = {}  # 局部变量
        self.used_globals: Dict[str, Variable] = {}

        self.ret: Optional[Variable] = None

        # 调用：callee -> list of arg_list
        self.calls: Dict[str, List[List[Variable]]] = {}

        # Base 集合（本函数内部直接读写）
        self.r_base: Set[Variable] = set()
        self.w_base: Set[Variable] = set()

        # Total 集合（包含传播）
        self.r_total: Set[Variable] = set()
        self.w_total: Set[Variable] = set()

        # 用于判断“读前是否已写”
        self._written_names = set()

    # =====================================
    #   基础 API
    # =====================================

    def add_param(self, var: Variable):
        self.params.append(var)

    def set_ret(self, var: Variable):
        self.ret = var

    def add_call(self, callee_name: str, args: List[Variable]):
        if callee_name not in self.calls:
            self.calls[callee_name] = []
        self.calls[callee_name].append(args)

    def mark_read(self, var: Variable):
        """
        r_base 规则：
        - 指针：直接算读
        - 非指针：若该变量名已经被写，则不算 r_base
        """
        if var.is_pointer:
            self.r_base.add(var)
            return

        if var.name in self._written_names:
            return

        self.r_base.add(var)
        print("mark read!!!", var)

    def mark_write(self, var: Variable):
        """
        w_base 规则：
        - 指针：修改地址 / 内容均算写
        """
        self.w_base.add(var)
        self._written_names.add(var.name)
        print("mark write!!!", var)


    # =====================================
    #   传播计算（★★核心功能★★）
    # =====================================
    def compute_propagation(self, system_map: Dict[str, "FunctionUnit"]):
        """
        计算 r_total / w_total。

        规则：
        1. 初始 total = base
        2. 对每个调用 callee：
            取 callee.r_total / callee.w_total
            根据 callee.params[i] 的位置，把它映射到本函数的 args[i]
            若 callee 的某个 total 中包含某个 param，则 arg 对应变量加入本函数 total
        """

        # ------ 初始化 total ------
        self.r_total = set(self.r_base)
        self.w_total = set(self.w_base)

        # ------ 处理每个子函数 ------
        for callee_name, call_list in self.calls.items():
            if callee_name not in system_map:
                continue  # 外部库函数，忽略

            callee_fu = system_map[callee_name]

            # 确保子函数 total 已经计算（避免递归顺序问题）
            # Note: 如果你有 DAG 调度最好外部处理
            if callee_fu.r_total == set() and callee_fu.r_base != set():
                callee_fu.compute_propagation(system_map)

            callee_params = callee_fu.params

            # ------- 遍历对同一函数的多次调用 -------
            for arg_list in call_list:

                # ------- 对子函数的每个形参做映射 -------
                for idx, param_var in enumerate(callee_params):

                    if idx >= len(arg_list):
                        break

                    arg_var = arg_list[idx]

                    # -------------------------------------------------------
                    # ★ 传播 READ
                    # -------------------------------------------------------
                    for child_read in callee_fu.r_total:
                        if child_read.name == param_var.name:
                            # 子函数读 param → 本函数读 arg
                            self.r_total.add(arg_var)

                    # -------------------------------------------------------
                    # ★ 传播 WRITE
                    # -------------------------------------------------------
                    for child_write in callee_fu.w_total:
                        if child_write.name == param_var.name:
                            self.w_total.add(arg_var)

        # --- end compute_propagation ---
        return self

    
    def is_io(self, var: Variable) -> bool:
        """
        I/O：既出现在 r_total 又出现在 w_total 即视为 I/O。
        判断方式：仅根据 name 一致即可（你之前的语义）
        """
        name = var.name

        in_r = any(v.name == name for v in self.r_total)
        in_w = any(v.name == name for v in self.w_total)

        return in_r and in_w

    # =====================================
    def __repr__(self):
        return (f"FunctionUnit(name={self.name}, "
                f"params={self.params}, "
                f"calls={self.calls})")
