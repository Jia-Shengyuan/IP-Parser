import argparse
import clang.cindex
from pathlib import Path

from core.variable import Variable, Domain, VarKind
from core.function_unit import FunctionUnit
from core.system_context import SystemContext


# ============================================================
# Helper Functions
# ============================================================
def is_in_file(cursor, file_path):
    return cursor.location.file and cursor.location.file.name == file_path


def collect_globals(cursor, file_path):
    """
    扫描全局变量 → {name: Variable}
    """
    globals_map = {}

    for c in cursor.get_children():
        if c.kind == clang.cindex.CursorKind.VAR_DECL and is_in_file(c, file_path):
            if c.semantic_parent.kind == clang.cindex.CursorKind.TRANSLATION_UNIT:
                globals_map[c.spelling] = Variable.from_cursor(c)

    return globals_map


def parse_argument_expr(expr_cursor):
    """
    抽取函数调用实参
    """

    # 变量引用
    if expr_cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
        return Variable.from_cursor(expr_cursor.referenced)

    # 取地址 &x
    if expr_cursor.kind == clang.cindex.CursorKind.UNARY_OPERATOR:
        for child in expr_cursor.get_children():
            v = parse_argument_expr(child)
            if v:
                v.is_pointer = True
                return v

    # 字面量
    if expr_cursor.kind in (
        clang.cindex.CursorKind.INTEGER_LITERAL,
        clang.cindex.CursorKind.FLOATING_LITERAL,
        clang.cindex.CursorKind.STRING_LITERAL,
    ):
        token_str = ' '.join(t.spelling for t in expr_cursor.get_tokens())
        return Variable(token_str, domain=None, kind=VarKind.BUILTIN, is_pointer=False)

    # fallback
    token_str = ' '.join(t.spelling for t in expr_cursor.get_tokens()) or "<unknown>"
    return Variable(token_str, domain=None, kind=VarKind.BUILTIN, is_pointer=False)


def find_callee(expr_cursor):
    """
    递归找到 CALL_EXPR 的目标函数名
    """
    if expr_cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
        if expr_cursor.referenced and expr_cursor.referenced.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            return expr_cursor.spelling

    for ch in expr_cursor.get_children():
        r = find_callee(ch)
        if r:
            return r

    return None


# ============================================================
# 函数体扫描
# ============================================================
def scan_function_body(cursor, func_unit, file_path,
                       locals_set, globals_map, globals_used):

    if not is_in_file(cursor, file_path):
        return

    # 局部变量声明
    if cursor.kind == clang.cindex.CursorKind.VAR_DECL:
        v = Variable.from_cursor(cursor)
        if v.domain == Domain.LOCAL:
            locals_set[v.name] = v

            # 有初始化也按写
            children = list(cursor.get_children())
            func_unit.mark_write(v)
        return

    # 赋值写
    if cursor.kind == clang.cindex.CursorKind.BINARY_OPERATOR:
        if "=" in [t.spelling for t in cursor.get_tokens()]:
            children = list(cursor.get_children())
            if children:
                lhs_var = parse_argument_expr(children[0])
                func_unit.mark_write(lhs_var)

    # 变量读
    if cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
        name = cursor.spelling

        if name in globals_map:
            v = globals_map[name]
            globals_used[name] = v
            func_unit.mark_read(v)
        elif name in locals_set:
            func_unit.mark_read(locals_set[name])
        else:
            # 参数
            for p in func_unit.params:
                if p.name == name:
                    func_unit.mark_read(p)

    # return
    if cursor.kind == clang.cindex.CursorKind.RETURN_STMT:
        children = list(cursor.get_children())
        if children:
            func_unit.set_ret(parse_argument_expr(children[0]))
        else:
            func_unit.set_ret(Variable("void", None, VarKind.BUILTIN, is_pointer=False))

    # 函数调用
    if cursor.kind == clang.cindex.CursorKind.CALL_EXPR:
        callee = find_callee(cursor)
        args = [parse_argument_expr(arg) for arg in cursor.get_arguments()]

        if callee:
            func_unit.add_call(callee, args)

        for arg in args:
            func_unit.mark_read(arg)

    # 递归
    for child in cursor.get_children():
        scan_function_body(child, func_unit, file_path,
                           locals_set, globals_map, globals_used)


# ============================================================
# 扫描函数
# ============================================================
# ============================================================
# 扫描函数
# ============================================================
def scan_functions(cursor, file_path, globals_map, ctx: SystemContext):

    if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:

        if cursor.location.file is None or cursor.location.file.name != file_path:
            return

        if not cursor.is_definition():
            return

        # -----------------------------
        # 构造准确的函数 API 字符串（带返回值）
        # -----------------------------
        # 获取返回值类型
        ret_type = cursor.result_type.spelling if cursor.result_type else "void"

        # 创建 FunctionUnit 先不填 api
        func = FunctionUnit(cursor.spelling)

        # 添加形参对象
        param_objs = []
        for c in cursor.get_children():
            if c.kind == clang.cindex.CursorKind.PARM_DECL:
                var = Variable.from_cursor(c)
                func.add_param(var)
                param_objs.append(var)

        # 使用 Variable.type 构造参数字符串
        param_strs = []
        for p in param_objs:
            # 指针类型加 *
            pointer_suffix = "*" if p.is_pointer and "*" not in p.type else ""
            param_strs.append(f"{p.type}{pointer_suffix} {p.name}")

        api_str = f"{ret_type} {func.name}({', '.join(param_strs)})"
        func.api = api_str  # 填充 FunctionUnit.api

        locals_set = {}
        globals_used = {}
        has_body = False

        for c in cursor.get_children():
            if c.kind == clang.cindex.CursorKind.COMPOUND_STMT:
                has_body = True
                scan_function_body(c, func, file_path,
                                   locals_set, globals_map, globals_used)

        if has_body:
            func.locals = locals_set
            func.used_globals = globals_used
            ctx.add_function(func)

    # 递归扫描子节点
    for child in cursor.get_children():
        scan_functions(child, file_path, globals_map, ctx)




# ============================================================
# 单文件处理
# ============================================================
def process_c_file(file_path: str, ctx: SystemContext):
    index = clang.cindex.Index.create()
    tu = index.parse(file_path, args=['-std=c11'])

    print(f"\n=== 扫描文件: {file_path} ===\n")

    globals_map = collect_globals(tu.cursor, file_path)
    for g in globals_map.values():
        ctx.add_global(g)

    scan_functions(tu.cursor, file_path, globals_map, ctx)


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="函数级分析器")
    parser.add_argument("--root-dir", required=True)
    args = parser.parse_args()

    root = Path(args.root_dir)
    c_files = list(root.rglob("*.c"))

    ctx = SystemContext()

    for c in c_files:
        process_c_file(str(c), ctx)

    print("\n=== Running Fix-point Analysis Pipeline ===")
    ctx.run_analysis_pipeline()

    ctx.dump()
    print("\n扫描完成！")


if __name__ == "__main__":
    main()
