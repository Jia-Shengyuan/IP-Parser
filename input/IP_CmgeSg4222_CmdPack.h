#ifndef IP_CMGESG4222_CMDPACK_H
#define IP_CMGESG4222_CMDPACK_H

#include <stdio.h> // 示例: 添加通用头文件

#include "common.h"

/* --- 类型定义 --- */
typedef unsigned char       unint08;
typedef unsigned int        unint32;
typedef int                 siint32;

/* --- 全局变量定义 --- */

/* --- 函数原型 --- */
void CmgeSg4222_CmdPack(unint08 *cmdOut, unint32 idx);

#endif // IP_CMGESG4222_CMDPACK_H