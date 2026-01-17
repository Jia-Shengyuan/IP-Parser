#include <stdio.h>

// 叶节点函数：不调用其他函数
int leaf_func_a(int x) {
    return x + 1;
}

// 叶节点函数：不调用其他函数
int leaf_func_b(int x) {
    return x * 2;
}

// 中间层函数：调用叶节点函数
int mid_func_1(int a, int b) {
    int result = leaf_func_a(a);
    result += leaf_func_b(b);
    return result;
}

// 中间层函数：调用叶节点函数
int mid_func_2(int x) {
    return leaf_func_a(x) + leaf_func_b(x);
}

// 顶层函数：调用中间层函数
int top_func(int a, int b, int c) {
    int r1 = mid_func_1(a, b);
    int r2 = mid_func_2(c);
    return r1 + r2;
}

// 入口函数
int main() {
    int result = top_func(1, 2, 3);
    printf("Result: %d\n", result);
    return 0;
}
