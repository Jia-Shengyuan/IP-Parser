#include "a.h"

int x[10] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
int *p = &x[4];

enum Color { RED, GREEN, BLUE };

enum Color favorite_color = GREEN;

union TestUnion {
    int i;
    float f;
    enum Color c;
} test_union;

void traverse() {
    int i = 5; // non-constant during compile time
    int y = x[i]; // should be viewed as x[?]
}

void call_add() {
    int result = add(x[2], x[3]);
    // int w = *p;
    *p += 1;
    favorite_color = BLUE;
    // *p = (*p) + 1;
}

volatile int _a, _b;

void f1(int* ptr) {
    *ptr = 1;
    test_union.i = 10;
}

void f2(int* ptr) {
    f1(_a);
    *ptr = 2;
}

void f3() {
    // int *ptr = &_b;
    // f1(ptr);
    f1(&_b);
}