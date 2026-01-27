#include "common.h"

int a[3];
int *ptr = &a[0];

void f(int *p) {
    p[0] = 1;
}

void g() {
    // ptr = a;
    f(a);
}