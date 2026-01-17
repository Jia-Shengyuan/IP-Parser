#include "a.h"

extern int x[10];

int add(int a, int b) {
    return a + b;
}

double sq(double v) {
    return v * v;
}

struct Vector2 {
    int x, y;
};

typedef struct {
    int x, y, z;
} Vector3;

typedef int Integer;
typedef int Array5[5];

typedef struct VEC_3X3X3 {
    Vector3 x[3];
    struct Vector2 *y[3];
    Vector3 z[3];
} Huge;

Vector3 vec[2];
Integer integer;

void scaleX() {
    vec[0].x *= integer;
}

void fun2() {
    // x[4] = integer;
    int *ptr = &x[2];
    x[1] = 10;
    int *pptr = &x[4];
    *pptr = integer;
    pptr = ptr;
    *pptr = 20;
}

void func_with_ptr(int* ptr, Vector3* arg) {
    *ptr += arg->y;
    x[4] = 1;
}

void call_func_with_ptr() {
    p = &x[3];
    func_with_ptr(&x[3], &vec[1]);
}