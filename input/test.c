#include "common.h"

int a[3];

void f(double d) {
    d++;
}

void g(int *x) {
    int i=0;
}

void modify(int num) {
    f((double)(num+__var));
}