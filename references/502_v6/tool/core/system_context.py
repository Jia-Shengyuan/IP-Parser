# core/system_context.py
from typing import Dict, Set
from core.function_unit import FunctionUnit
from core.variable import Variable


class SystemContext:

    def __init__(self):
        self.functions: Dict[str, FunctionUnit] = {}
        self.globals: Dict[str, Variable] = {}

        # ★ 新增：所有函数的输出接口变量合集
        self.global_out_set: Set[Variable] = set()

    def add_global(self, var: Variable):
        self.globals[var.name] = var

    def add_function(self, f: FunctionUnit):
        self.functions[f.name] = f

    # ============================================================
    # ★★ 新增：不动点迭代分析 ★★
    # ============================================================
    def run_analysis_pipeline(self):
        """
        fix-point iteration:
        反复调用 compute_propagation() 直到所有函数的 r_total / w_total 稳定
        """

        changed = True
        iteration = 0

        while changed:
            iteration += 1
            changed = False
            print(f"  Iteration {iteration}...")

            for f in self.functions.values():

                old_r = set(v.name for v in f.r_total)
                old_w = set(v.name for v in f.w_total)

                f.compute_propagation(self.functions)

                new_r = set(v.name for v in f.r_total)
                new_w = set(v.name for v in f.w_total)

                if old_r != new_r or old_w != new_w:
                    changed = True

        print("  -> Fix-point reached")

    # ============================================================
    def dump(self):
        print("\n================ SYSTEM CONTEXT ================")
        print("全局变量 G:")
        if self.globals:
            for g in self.globals.values():
                print(f"  - {g.name} (is_ptr={g.is_pointer})")
        else:
            print("  (无全局变量)")

        print("\n函数集合 S:")
        for fname in self.functions:
            print(f"  - {fname}")

        print("\n==================== 所有函数 F ====================")
        for fname, f in self.functions.items():
            print("=" * 60)
            print(f"[FunctionUnit]  函数名: {f.name}")
            print("-" * 60)

            print("  [Params]")
            for p in f.params:
                print(f"    - {p.name}, scope={p.scope.name}, ptr={p.is_pointer}")

            print("  [Locals]")
            for ln, lv in f.locals.items():
                print(f"    - {ln}, scope={lv.scope.name}, ptr={lv.is_pointer}")

            print("  [Globals Used]")
            for gn in f.used_globals:
                print(f"    - {gn}")

            print("  [Return]")
            if f.ret:
                print(f"    - {f.ret.name}, ptr={f.ret.is_pointer}")

            print("  [R_BASE]")
            for v in f.r_base:
                print(f"    - {v.name} (ptr={v.is_pointer})")

            print("  [W_BASE]")
            for v in f.w_base:
                print(f"    - {v.name} (ptr={v.is_pointer})")

            print("  [R_TOTAL]")
            for v in f.r_total:
                print(f"    - {v.name}")

            print("  [W_TOTAL]")
            for v in f.w_total:
                print(f"    - {v.name}")

            print("  [Calls]")
            for callee, calls in f.calls.items():
                print(f"    {callee}: {len(calls)} 次调用")

        # ★ 新增输出 global_out_set
        print("\n================ GLOBAL OUT SET ================")
        for v in self.global_out_set:
            print(f"  - {v.name}  (ptr={v.is_pointer})")

    def classify_interfaces(self):
        """
        遍历所有函数：
        - 执行 classify_out_variable()
        - 执行 classify_param_variable()
        返回结构：
        {
            function_name: {
                "out":  [...],
                "param": [...]
            }
        }
        """

        # print("\n===================== INTERFACE CLASSIFICATION =====================")

        results = {}
        self.global_out_set.clear()   # 重置 OUT 集合

        for fname in self.functions.keys():
            # print(f"\n------------------- Function: {fname} -------------------")
            out_vars = self.classify_out_variable(fname)
            param_vars = self.classify_param_variable(fname)
            in_vars = self.classify_in_variable(fname)
            inout_vars = self.classify_inout_variable(fname)
            state_vars = self.classify_state_variable(fname)

            results[fname] = {
                "out": out_vars,
                "param": param_vars,
                "in_vars": in_vars,
                "inout_vars": inout_vars,
                "state_vars": state_vars,
                
            }
            # print(results)

        # print("\n=================== END INTERFACE CLASSIFICATION ===================\n")
        return results


    # =====================================================================
    #    classify_out_variable
    # =====================================================================
    def classify_out_variable(self, fname: str):
        """
        找出函数 fname 的“输出变量”，定义如下：
        1) 变量 ∈ w_total
        2) 变量 ∉ r_total
        3) 如果函数有返回值，则只有返回值对应的变量才算作为 RETURN 类型的 out-variable
        """

        if fname not in self.functions:
            print(f"[ERROR] classify_out_variable: function '{fname}' not found")
            return []
        # print(fname)

        fu = self.functions[fname]
        # print(f"\n[OUT Variable] Function: {fname}")

        out_vars = []

        r_names = {v.name for v in fu.r_total}
        w_names = {v.name for v in fu.w_total}
        # print("w_names", w_names)
        # print(fu.used_globals.items())
        # print("self.globals",self.globals)

        # 收集所有变量（params + locals + used globals）
        all_vars = {
            **{p.name: p for p in fu.params},
            **{ln: lv for ln, lv in fu.locals.items()},
            **{gn: gv for gn, gv in fu.used_globals.items()},
        }

        # 返回值名字（如果有返回值）
        ret_name = fu.ret.name if (fu.ret is not None and hasattr(fu.ret, "name")) else None

        # ---- 判定 out-variable ----
        for vname, var in all_vars.items():
            is_write_only = (vname in w_names and vname not in r_names)
            is_return = (ret_name is not None and vname == ret_name)

            if is_write_only or is_return:
                tag = "WRITE-only" if is_write_only else "RETURN"
                # print(f"  - {vname:<20}  [{tag}]")

                out_vars.append(var)
                self.global_out_set.add(var)

        return out_vars



    # =====================================================================
    #    classify_param_variable
    # =====================================================================
    def classify_param_variable(self, fname: str):
        """
        找出某函数 fname 内满足以下条件的“输入变量”：
        - ∈ r_total
        - ∉ global_out_set
        - ∈ 全局变量 self.globals
        """

        if fname not in self.functions:
            print(f"[ERROR] classify_param_variable: function '{fname}' not found")
            return []

        fu = self.functions[fname]
        # print(f"\n[PARAM Variable] Function: {fname}")

        r_names = {v.name for v in fu.r_total}
        self_out_names = {v.name for v in fu.w_total}
        out_names = {v.name for v in self.global_out_set}
        global_names = set(self.globals.keys())  # 全局变量名
        matched = []

        # 收集所有变量（参数 + 局部变量 + 使用到的全局变量）
        all_vars = {
            **{p.name: p for p in fu.params},
            **{ln: lv for ln, lv in fu.locals.items()},
            **{gn: gv for gn, gv in fu.used_globals.items()},
        }

        # ---- 判定 param-variable ----
        for vname, var in all_vars.items():
            cond_read = (vname in r_names)
            cond_not_self_out = (vname not in self_out_names)
            cond_not_out = (vname not in out_names)
            cond_global = (vname in global_names)

            if cond_read and cond_not_self_out and cond_not_out and cond_global:
                # print(f"  - {vname:<20}  [READ & not Write & not OUT & GLOBAL]")
                matched.append(var)

        return matched


    # =====================================================================
    #    classify_in_variable
    # =====================================================================
    def classify_in_variable(self, fname: str):
        """
        找出某函数 fname 内满足以下条件的“输入变量”：
        - ∈ r_total
        - ∉ global_out_set
        - ∈ 全局变量 self.globals
        """

        if fname not in self.functions:
            print(f"[ERROR] classify_param_variable: function '{fname}' not found")
            return []

        fu = self.functions[fname]
        # print(f"\n[in Variable] Function: {fname}")
        print(fname)


        r_names = {v.name for v in fu.r_total}
        self_out_names = {v.name for v in fu.w_total}
        out_names = {v.name for v in self.global_out_set}
        global_names = set(self.globals.keys())  # 全局变量名
        matched = []
        print("rname", r_names)

        # 收集所有变量（参数 + 局部变量 + 使用到的全局变量）
        all_vars = {
            **{p.name: p for p in fu.params},
            **{ln: lv for ln, lv in fu.locals.items()},
            **{gn: gv for gn, gv in fu.used_globals.items()},
        }

        # ---- 判定 param-variable ----
        for vname, var in all_vars.items():
            cond_read = (vname in r_names)
            cond_not_self_out = (vname not in self_out_names)

            if cond_read and cond_not_self_out:
                # print(f"  - {vname:<20}  [READ & not Write]")
                matched.append(var)
    
        return matched

    # =====================================================================
    #    classify_inout_variable
    # =====================================================================
    def classify_inout_variable(self, fname: str):
        """
        找出某函数 fname 内满足以下条件的“输入变量”：
        - ∈ r_total
        - ∉ global_out_set
        - ∈ 全局变量 self.globals
        """

        if fname not in self.functions:
            print(f"[ERROR] classify_param_variable: function '{fname}' not found")
            return []

        fu = self.functions[fname]
        # print(f"\n[inout Variable] Function: {fname}")

        r_names = {v.name for v in fu.r_total}
        self_out_names = {v.name for v in fu.w_total}
        out_names = {v.name for v in self.global_out_set}
        global_names = set(self.globals.keys())  # 全局变量名
        matched = []

        # 收集所有变量（参数 + 局部变量 + 使用到的全局变量）
        all_vars = {
            **{p.name: p for p in fu.params},
            **{ln: lv for ln, lv in fu.locals.items()},
            **{gn: gv for gn, gv in fu.used_globals.items()},
        }

        # ---- 判定 param-variable ----
        for vname, var in all_vars.items():
            cond_read = (vname in r_names)
            cond_self_out = (vname in self_out_names)

            if cond_read and cond_self_out:
                # print(f"  - {vname:<20}  [READ & Write]")
                matched.append(var)
    
        return matched

    # =====================================================================
    #    classify_state_variable
    # =====================================================================
    def classify_state_variable(self, fname: str):
        """
        找出某函数 fname 内满足以下条件的“输入变量”：
        - ∈ r_total
        - ∉ global_out_set
        - ∈ 全局变量 self.globals
        """

        if fname not in self.functions:
            print(f"[ERROR] classify_param_variable: function '{fname}' not found")
            return []

        fu = self.functions[fname]
        # print(f"\n[state Variable] Function: {fname}")

        r_names = {v.name for v in fu.r_total}
        self_out_names = {v.name for v in fu.w_total}
        out_names = {v.name for v in self.global_out_set}
        global_names = set(self.globals.keys())  # 全局变量名
        matched = []

        # 收集所有变量（参数 + 局部变量 + 使用到的全局变量）
        all_vars = {
            **{gn: gv for gn, gv in fu.used_globals.items()},
        }

        # ---- 判定 param-variable ----
        for vname, var in all_vars.items():
            cond_read = (vname in r_names)
            cond_self_out = (vname in self_out_names)

            if cond_read and cond_self_out:
                # print(f"  - {vname:<20}  [READ & Write]")
                matched.append(var)
    
        return matched