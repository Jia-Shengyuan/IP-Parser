//#include "IP_AccSinTrackCalculate.h"

// =======================================================
// 函数实现
// =======================================================
#include <stdio.h> // 示例: 添加通用头文件

//#include "common2.h"




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

// 绝对值：直接返回 x
#define Fabsx(x)    (x)

// 平方根：直接返回 x
#define Sqrtx(x)    (x)

// 符号函数：直接返回 x
#define Sgn2(x)     (x)

// 正弦函数：直接返回 x
#define Sinx(x)     (x)

// 余弦函数：直接返回 x
#define Cosx(x)     (x)


void AccSinTrackInit(SMnvrData *past)
{
    float64 tacc;
    float64 tv;

    /* 计算加/减速段时间 */
    tacc = 2.0 * Fabsx(past->dChimax / past->amax);
    tv = Fabsx((past->Chim - past->Chim0) / past->dChimax) - tacc;

    /* 对无匀速段情况的处理 */
    if(tv <= 0.0)
    {
        tv = 0.0;

        tacc = Sqrtx(2.0 * Fabsx((past->Chim - past->Chim0) / past->amax));
    }

    /* 计算期望角速度轨迹的相对转折时间点tm1 */
    past->tm1p = tacc;

    /* 计算期望角速度轨迹的相对转折时间点tm2 */
    past->tm2p = tacc + tv;

    /* 计算期望角速度轨迹的相对转折时间点tm3 */
    past->tm3p = 2.0 * tacc + tv;

    return;
}

void AccSinTrackCalculate(SMnvrData *past, float64 dtv, float64 dtTr)
{
    float64 f;
    float64 rf;
    float64 rff;
    float64 sign;
    float64 tm;

    if(past->F_Init_Trajectory == 1)
    {
        past->F_Init_Trajectory = 0;
        AccSinTrackInit(past);
    }

    f = DBL_PI / past->tm1p;
    sign = Sgn2(past->Chim - past->Chim0);
    rf = 1.0 / f;
    rff = 1.0 / (f * f);

    /* 机动角度轨迹规划 */
    tm = past->tmA;
    if(tm < 0.0)  /* 机动开始前 tm < 0 */
    {
        past->Chi_Ref = past->Chim0;
    }
    /* 0 <= tm < tm1p */
    else if(tm < past->tm1p)  /* 加速段 */
    {
        past->Chi_Ref  = past->Chim0 + 0.5 * sign * past->amax * (0.5 * tm * tm - rff + rff * Cosx(f * tm));
    }
    /* tm1p <= tm < tm2p */
    else if(tm < past->tm2p)  /* 匀速段 */
    {
        past->Chi_Ref  = past->Chim0 +  0.5 * sign * past->amax * (tm * past->tm1p - 0.5 * past->tm1p * past->tm1p);
    }
    /* tm2p <= tm < tm3p */
    else if(tm < past->tm3p)  /* 减速段 */
    {
        past->Chi_Ref  = past->Chim0 - 0.5 * sign * past->amax * (0.5 * tm * tm - past->tm3p * tm + rff * Cosx(f * (tm - past->tm2p)) - rff + past->tm1p * past->tm1p + 0.5 * past->tm3p * (past->tm2p - past->tm1p));
    }
    /* tm >= tm3p */
    else  /* 机动到位后 */
    {
        past->Chi_Ref = past->Chim;
    }

    /* 机动角速度轨迹规划 */
    tm = past->tmA - dtv;
    if(tm < 0.0)  /* 机动开始前 tm < 0 */
    {
        past->dChi_Ref = 0.0;
    }
    /* 0 <= tm < tm1p */
    else if(tm < past->tm1p)  /* 加速段 */
    {
        past->dChi_Ref = 0.5 * sign * past->amax * (tm - rf * Sinx(f * tm));
    }
    /* tm1p <= tm < tm2p */
    else if(tm < past->tm2p)  /* 匀速段 */
    {
        past->dChi_Ref = 0.5 * sign * past->amax * past->tm1p;
    }
    /* tm2p <= tm < tm3p */
    else if(tm < past->tm3p)  /* 减速段 */
    {
        past->dChi_Ref = -0.5 * sign * past->amax * (tm - past->tm3p - rf * Sinx(f * (tm - past->tm2p)));
    }
    /* tm >= tm3p */
    else  /* 机动到位后 */
    {
        past->dChi_Ref = 0.0;
    }

    /* 机动角加速度轨迹规划 */
    tm = past->tmA + dtTr;
    if(tm < 0.0)  /* 机动开始前 tm < 0 */
    {
        past->acc_Ref = 0.0;
    }
    /* 0 <= tm < tm1p */
    else if(tm < past->tm1p)  /* 加速段 */
    {
        past->acc_Ref = 0.5 * sign * past->amax * (1.0 - Cosx(f * tm));
    }
    /* tm1p <= tm < tm2p */
    else if(tm < past->tm2p)  /* 匀速段 */
    {
        past->acc_Ref = 0.0;
    }
    /* tm2p <= tm < tm3p */
    else if(tm < past->tm3p)  /* 减速段 */
    {
        past->acc_Ref = -0.5 * sign * past->amax * (1.0- Cosx(f * (tm - past->tm2p)));
    }
    /* tm >= tm3p */
    else  /* 机动到位后 */
    {
        past->acc_Ref = 0.0;
    }

    return;
}