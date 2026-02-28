
typedef struct {
    int* ptr;
} Ptr;

int a, b;

void change_ptr(Ptr* p, int* new_ptr) {
    p->ptr = new_ptr;
}

void recurse_change_ptr(Ptr* p, int* new_ptr) {
    change_ptr(p, new_ptr);
}

void call_change_ptr() {
    Ptr p;
    p.ptr = &a;
    recurse_change_ptr(&p, &b);
    *p.ptr = 1;
}