#include "a.h"

extern int x[10];

int add(int a, int b) {
    return a + b;
}

double sq(double x) {
    return x * x;
}

struct Vector2 {
    int x, y;
};

typedef struct {
    int x, y, z;
} Vector3;

typedef int Integer; // Can't be handled correctly yet

typedef struct VEC_3X3X3 {
    Vector3 x[3];
    struct Vector2 *y[3];
    Vector3 z[3];
} Huge; // abstract size = 3*3 + 3 + 3*3 = 21