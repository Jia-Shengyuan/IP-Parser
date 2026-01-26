#ifndef IP_ACCSINTRACKCALCULATE_H
#define IP_ACCSINTRACKCALCULATE_H

#include <stdio.h> // 示例: 添加通用头文件

#include "common.h"

/* --- 类型定义 --- */
typedef unsigned int        unint32;
typedef double              float64;
typedef  struct TAG_SMNVRDATA
{
    /* 输入数据 浮点 */
    float64 tmA;                        /* 机动起始时刻 tmA       相对时刻   */
    float64 dChimax;                    /* 期望的最大机动角速度    dχmax     */
    float64 Chim;                       /* 机动的目标姿态角        χm        */
    float64 Chim0;                      /* 机动起始时的姿态角      χm0       */
    float64 amax;                       /* 期望的最大机动角加速度            */

    /* 输出数据 浮点 */
    float64 acc_Ref;                    /* 规划的机动角加速度      a_Ref      */
    float64 dChi_Ref;                   /* 规划的机动角速度        dχ_Ref    */
    float64 Chi_Ref;                    /* 规划的机动角度          χ_Ref     */

    /* 输入输出数据 浮点 */
    float64 tm1p;                       /* 加速段转折点时刻（以tm_xin为基准的相对时刻） */
    float64 tm2p;                       /* 匀速段转折点时刻（以tm_xin为基准的相对时刻） */
    float64 tm3p;                       /* 结束点时刻      （以tm_xin为基准的相对时刻） */
    float64 t_sinacc;                   /* t_sinacc */
    float64 t_conacc;                   /* t_conacc */

    /*  */
    float64 t_m1a;                      /* 加速段时刻 */
    float64 t_m1b;                      /* 匀速段时刻 */
    float64 t_m3a;                      /* 减速段时刻 */
    float64 t_m3b;                      /* 匀速段时刻 */

    /* 输入输出数据 整型 */
    unint32 F_Init_Trajectory;          /* 轨迹规划是否需要初始化，1：需要；0：不需要 */

} SMnvrData;
typedef int                 siint32;

/* --- 全局变量定义 --- */
const float64 DBL_PI        = 6.283185307179586;

/* --- 函数原型 --- */
void AccSinTrackCalculate(SMnvrData *past, float64 dtv, float64 dtTr);
void AccSinTrackInit(SMnvrData *past);

#endif // IP_ACCSINTRACKCALCULATE_H