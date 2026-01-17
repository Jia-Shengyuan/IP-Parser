#include "a.h"

int x[10] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
int *p = &x[4];

void traverse() {
    int i = 5; // non-constant during compile time
    int y = x[i]; // should be viewed as x[?]
}