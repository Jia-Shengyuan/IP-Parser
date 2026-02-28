typedef unsigned int unint32;
typedef int siint32;
typedef double float64;

typedef struct SItem {
    unint32 id;
    float64 vec[3];
} SItem;

typedef struct SPacket {
    SItem items[4];
    unint32 flags[8];
} SPacket;

typedef struct SNode {
    SPacket packet;
    float64 hist[2][3];
} SNode;

SPacket gPackets[10];
SNode gNodes[6];
int gIntBuf[16];

void case_struct_array(siint32 i, siint32 j)
{
    unint32 v = gPackets[i].items[j].id;
    gPackets[i].items[j].id = v + 1;
    gPackets[i].items[j].vec[2] = gPackets[i].items[0].vec[j];
}

void case_struct_with_array_member(siint32 k)
{
    float64 t = gNodes[1].hist[k][2];
    gNodes[1].hist[k][1] = t + 1.0;

    unint32 f = gNodes[1].packet.flags[k];
    gNodes[1].packet.flags[k] = f + 3;
}

void case_array_of_struct_with_array_member(siint32 a, siint32 b)
{
    gNodes[a].packet.flags[b] = gNodes[a].packet.items[0].id;
    gNodes[a].packet.items[b].vec[1] = gNodes[a].hist[0][b];
}

void case_ptr_param_used_as_array(SItem *pItems, siint32 idx)
{
    pItems[idx].id = pItems[idx].id + 1;
    pItems[idx].vec[1] = pItems[0].vec[idx];
}

void case_ptr_struct_with_array_member(SPacket *pPacket, siint32 i, siint32 j)
{
    pPacket[i].flags[j] = pPacket[i].flags[j] + 1;
    pPacket[i].items[j].vec[0] = pPacket[0].items[i].vec[2];
}

void case_b_use_param_as_array(int *buf, siint32 idx)
{
    buf[idx] = buf[idx] + 10;
    buf[0] = buf[idx] + buf[1];
}

void case_a_pass_pointer_to_b(int *p, siint32 idx)
{
    case_b_use_param_as_array(p, idx);
}

void case_pointer_alias_assign(int *q, siint32 i)
{
    int *p = q;
    p[i] = p[i] + 1;
    p[0] = q[i] + p[1];
}

void case_callers(void)
{
    siint32 i = 2;
    siint32 j = 3;

    case_struct_array(i, j);
    case_struct_with_array_member(j);
    case_array_of_struct_with_array_member(i, j);

    case_ptr_param_used_as_array(&gPackets[0].items[0], j);
    case_ptr_struct_with_array_member(&gPackets[0], i, j);
    case_a_pass_pointer_to_b(&gIntBuf[0], j);
    case_pointer_alias_assign(&gIntBuf[0], i);
}

void f_pointer_pointer(int **p, int *q) {
    *p = q;
}

void case_pointer_pointer(int *ptr) {
    f_pointer_pointer(&ptr, &gIntBuf[0]);
}
