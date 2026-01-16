#ifndef IP_B_TCPROCESS_H
#define IP_B_TCPROCESS_H

#include <stdio.h> // 示例: 添加通用头文件

#include "common.h"

/* --- 类型定义 --- */
typedef unsigned char   unint08;
typedef unsigned long   unint32;

/* --- 全局变量定义 --- */

/* --- 函数原型 --- */
void B_TcProcess(unint08* tcaData);
void CheckCal(const unint32 len, const unint08 *pkv, unint08 *chksum);

#endif // IP_B_TCPROCESS_H