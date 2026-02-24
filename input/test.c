#include "common.h"
#include <string.h>
#include <math.h>

unint32 a[3];
unint32 *ptr = &a[0];

const char* str1 = "hello world";
char str2[100];

typedef struct {
    int x;
    int y;
} Point;

Point points[3];

void test_array(int index) {
    unint32 x = a[index];
}

void test_struct_array(int index) {
    points[index].x = index;
    int y = points[0].y;
}

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