#include "common.h"
#include <string.h>
#include <math.h>

unint32 a[3];
unint32 *ptr = &a[0];

const char* str1 = "hello world";
char str2[100];

int my_strlen(const char* s) {
    int len = *s;
    return len;
}

void teststr(const char* cp) {
    int len = strlen(str1);
    strcpy(str2, str1);
}

void f(unint32 *p) {
    *p = 1;
}

void g() {
    int *q = (int*)(&a[2]);
    *q = 0;
    // ptr = a;
    // f(a);
}

typedef struct S_struct {
    unint32 b;
}S;

void h(int *v) {
    S* p = (S*)v;
    p->b = 2;
}

void h2(S* p) {
    int* v = (int*)p;
    *v = 3;
}

int* get() {
    return &a[0];
}

void modify() {
    int* p = get();
    *p = 4;
}