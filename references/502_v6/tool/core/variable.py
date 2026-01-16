from enum import Enum, auto
import clang.cindex

class Domain(Enum):
    GLOBAL = auto()
    PARAM = auto()
    LOCAL = auto()
    RETURN = auto()

class VarKind(Enum):
    POINTER = auto()
    RECORD = auto()
    ARRAY = auto()
    BUILTIN = auto()

class Variable:
    """
    Variable：变量的基础数据单元。
    """

    def __init__(self, name: str, domain: Domain, kind: VarKind, raw_type: str = None, is_pointer: bool = False):
        self.name = name
        self.domain = domain
        self.kind = kind
        self.raw_type = raw_type
        self.is_pointer = is_pointer
        self.pt = {}  # 指向表 (Points-To): Dict[str, int]

    def __repr__(self):
        return (
            f"Variable(name='{self.name}', "
            f"domain={self.domain.name if self.domain else 'None'}, "
            f"kind={self.kind.name if self.kind else 'None'}, "
            f"is_pointer={self.is_pointer}, "
            f"pt={self.pt})"
        )

    # ============================================
    # ⭐⭐ 静态辅助：从 Clang Cursor 自动构建 Variable
    # ============================================

    @staticmethod
    def detect_domain(cursor) -> Domain:
        """由 AST Cursor 判断 domain"""
        if cursor.kind == clang.cindex.CursorKind.PARM_DECL:
            return Domain.PARAM

        if cursor.semantic_parent.kind in (
            clang.cindex.CursorKind.TRANSLATION_UNIT,
            clang.cindex.CursorKind.UNEXPOSED_DECL
        ):
            return Domain.GLOBAL

        return Domain.LOCAL

    @staticmethod
    def detect_kind(cursor) -> VarKind:
        """从 Cursor 推断 VarKind"""
        if not hasattr(cursor, 'type'):
            return VarKind.BUILTIN

        k = cursor.type.kind
        if k == clang.cindex.TypeKind.POINTER:
            return VarKind.POINTER
        
        if k in (
            clang.cindex.TypeKind.CONSTANTARRAY,
            clang.cindex.TypeKind.INCOMPLETEARRAY,
            clang.cindex.TypeKind.VARIABLEARRAY, 
            clang.cindex.TypeKind.DEPENDENTSIZEDARRAY
        ):
            return VarKind.ARRAY

        canonical = cursor.type.get_canonical()
        if canonical.kind == clang.cindex.TypeKind.RECORD:
            return VarKind.RECORD
            
        return VarKind.BUILTIN

    @staticmethod
    def detect_pointer(cursor) -> bool:
        """判断是否为指针类型"""
        try:
            return cursor.type.kind == clang.cindex.TypeKind.POINTER
        except:
            return False

    # ============================================
    # ⭐⭐ 工厂函数：cursor → Variable
    # ============================================
    @classmethod
    def from_cursor(cls, cursor):
        """
        给一个 Clang cursor，自动推导变量属性并生成 Variable 实例
        """
        name = cursor.spelling
        domain = cls.detect_domain(cursor)
        kind = cls.detect_kind(cursor)
        pointer_flag = cls.detect_pointer(cursor)
        
        type_str = cursor.type.spelling if hasattr(cursor, 'type') else None
        
        return cls(name=name, domain=domain, kind=kind, raw_type=type_str, is_pointer=pointer_flag)

    # ============================================
    # ⭐⭐ 去重支持
    # ============================================
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return False
        return self.name == other.name
