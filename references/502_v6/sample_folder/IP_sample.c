#include "IP_sample.h"
int a;
const int b = 1;
int sample(int * p) {
    *p = a;
    a = b;
    int c = *p;
    return c;
}