
typedef struct {
    int* ptr;
} Ptr;

void test_ptr_config(int **ptr1, int *ptr2);

int a, b;

void do_nothing(Ptr* p, int * new_ptr) {

}

void change_ptr(Ptr* p, int* new_ptr) {
    p->ptr = new_ptr;
}

void recurse_change_ptr(Ptr* p, int* new_ptr) {
    change_ptr(p, new_ptr);
}

int *o1, *o2;

void change_target(int **ptr1, int *ptr2) {
    *ptr1 = ptr2;
}

void call_change_target(int *x, int *y) {
    o1 = x;
    o2 = y;
    change_target(&o1, o2);
    *o1 = 1;
}

void call_change_ptr() {
    Ptr p;
    p.ptr = &a;
    do_nothing(&p, &b);
    *p.ptr = 1;
}

void test_config(int *x, int *y) {
    o1 = x;
    o2 = y;
    test_ptr_config(&o1, o2);
    *o1 = 1;
}