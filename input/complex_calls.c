#include <stdio.h>

// 全局变量
int global_data[10];
int global_counter = 0;

// 叶子函数：没有调用其他函数
int increment(int x) {
    return x + 1;
}

// 叶子函数：没有调用其他函数
int double_value(int x) {
    return x * 2;
}

// 叶子函数：没有调用其他函数
void set_global(int index, int value) {
    global_data[index] = value;
}

// 中间层：调用叶子函数
int process_value(int x) {
    int step1 = increment(x);
    int step2 = double_value(step1);
    return step2;
}

// 中间层：调用叶子函数
void initialize_globals() {
    for (int i = 0; i < 5; i++) {
        set_global(i, i * 10);
    }
}

// 中间层：调用中间层
void full_initialize() {
    initialize_globals();
    global_counter = 5;
}

// 根函数：调用多个中间层函数
int compute_sum(int a, int b, int c) {
    int result = process_value(a) + process_value(b) + process_value(c);
    return result;
}

// 顶层：调用根函数
int main() {
    full_initialize();
    int sum = compute_sum(1, 2, 3);
    printf("Sum: %d\n", sum);
    return 0;
}
