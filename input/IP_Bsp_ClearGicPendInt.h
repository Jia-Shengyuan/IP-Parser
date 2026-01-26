#ifndef IP_BSP_CLEARGICPENDINT_H
#define IP_BSP_CLEARGICPENDINT_H

#include <stdio.h> // 示例: 添加通用头文件

#include "common.h"

/* --- 类型定义 --- */
typedef unsigned int			U32;
typedef volatile U32			V_U32;

/* --- 全局变量定义 --- */

/* --- 函数原型 --- */
void Bsp_ClearGicPendInt(U32 isrNo);

#endif // IP_BSP_CLEARGICPENDINT_H