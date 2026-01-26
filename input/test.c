
int a[3];

void f(double d) {
    d++;
}

void g(int *x) {
    int i=0;
}

void modify(int num) {
    g(&(a[0]));
}