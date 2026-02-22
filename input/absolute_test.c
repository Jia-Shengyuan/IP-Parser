typedef unsigned int uint32_t;

void foo(void) {
    volatile uint32_t val = *(volatile uint32_t*)0x01f80088;
    *(volatile uint32_t*)0x01f80088 = 0x5;
}
