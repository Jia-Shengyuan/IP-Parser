#ifndef IP_ATTITUDESELECTXY_H
#define IP_ATTITUDESELECTXY_H

#include <stdio.h> // 示例: 添加通用头文件

#include "common.h"

/* --- 类型定义 --- */
typedef int                 siint32;
typedef double              float64;
typedef unsigned int        unint32;
typedef __int64             llong64;
typedef struct TAG_ATTITUDE
{
/* 	float64 angleOrb[3];							 轨道系下的 */
    float64 angle[3];                                /* 三轴姿态角 */
	float64 angleB[3];                               /* 三轴姿态角偏置 */
	float64 angleBOld[3];                            /* 三轴姿态角偏置旧值，机动中使用 */
	float64 w[3];                                    /* 三轴姿态角速度 */
	float64 wB[3];                                   /* 三轴姿态角速度偏置 */
	float64 wBOld[3];                                /* 三轴姿态角速度偏置旧值 */
	float64 wbt[3];                                  /*  */
	
    float64 Cbr[3][3];                               /* 惯性指向偏置矩阵 */
    float64 Cbi[3][3];                               /* 星敏确定的惯性到本体的转换阵 */
	float64 Cbo[3][3];
	float64 Cbias[3][3];							/* 偏置矩阵 */
/* 	float64 Cbt[3][3];								本体系到目标系的转换矩阵 */
/*	float64 Cti[3][3];								  */
	float64 qbi[4];
	float64 qbr[4];
	float64 qTc[4];                                 /* 注入四元素 */
	float64 qTcOld[4];                              /* 注入四元素旧值 */

	unint32 flgXYIn;                                /* 滚动俯仰姿态输入选择标志 */
	unint32 flgZIn;                                 /* 偏航姿态输入选择标志 */
	unint32 bEnWin;                                 /* 角速度是否使用陀螺 */
} SAttitude;
typedef struct TAG_SENSOR_POWERONHEALTH
{
	unint32 FSH;         /* 敏感器健康状态 */
	unint32 FSP;         /* 敏感器加电时间满足 */
} SSensorPwrHealth;
typedef struct TAG_DSS
{
	unint32 flgXYSel;             /* XY选择 */
	unint32 flgZSel;              /* Z选择 */
    unint32 bSpxy;                /* TRUE32/FALSE32: 见太阳标志/未见太阳 */
	unint32 bSpz;                 /* TRUE32/FALSE32: 见太阳标志/未见太阳 */
	unint32 flgType;              /* Z轴太敏选择类型 */

	siint32 cntCHG;
	float64 angle[3];

	float64 anglePsi;             /* 几何定姿 */
	float64 angleGa[3];           /* 太敏陀螺定姿结果 */
	float64 angleSSF[3];

	SSensorPwrHealth pwrHealthXY[DSS_XY_NUM];

#if HAVE_DSSZ
	#if DSS_Z_NUM > 0
	SSensorPwrHealth pwrHealthZ[DSS_Z_NUM];
	#endif
#endif

} SDss;
typedef struct TAG_STS_DATA
{
	unint32 bUsable;                    /* 星敏测量数据的可用标志, TRUE32:可用, FALSE32:不可用 */
	unint32 bFvGroup;                   /* 双星敏比对无效标志 */

    float64 time;                       /* 星敏测量数据的星时 */
	float64 timePr1;                    /* 星敏上次测量数据的星时 */
    float64 q[4];                       /* 星敏原始测量信息 */

	float64 dltT;                       /* 星敏曝光时刻与星时差 */

	float64 axis0[3][3];                /* 星敏横轴和光轴计算 */
	float64 axis[3][3];              	/* 时间补偿之后的星敏横轴和光轴 */
	float64 dltAxis[3][3];              /* 时间补偿量计算 */

	float64 Csb_ex[3][3];               /* 经过一次补偿后的安装矩阵 */
	float64 Csb[3][3];                  /* 最终补偿后的安装矩阵 */
	float64 Csb_fix[3][3];              /* 标定到位后的安装矩阵 */

	float64 q_bi[4];                    /* 星敏惯性到本体测量信息 */
	float64 q_bi_fix[4];                /* 标定到位后的四元素 */
	float64 q_biPr1[4];                 /* 星敏惯性到本体测量信息 */
	float64 angle[3];                   /* 星敏计算的三轴姿态角（相对参考系） */
    float64 Cbi[3][3];					/* 星敏确定的惯性到本体的转换阵 */
    float64 Cbr[3][3];					/* 星敏确定的参考到本体的转换阵 */
	float64 Cbo[3][3];					/* 星敏确定的轨道到本体的转换阵 */

	unint32 bEnDelay;					/* 使能星敏延时补偿标志 */
	unint32 bWUsable;			        /* 星敏差分角速度可用标志 */
	float64 Tole[3];				    /* 星敏延时补偿角度 */
	float64 w_q[3];						/* 星敏差分的三轴角速度 */

	unint32 bCalied;                    /* 星敏标定到位标志 */
} SStsData;
typedef struct TAG_GYRO
{
	unint32 bValid3Axis;                  /* 3轴可用标志 */
	unint32 bSelXYZ;                      /* 正交陀螺选择 */       
	siint32 idxUsing[4];                  /* 记录使用的4个陀螺标号 */
	siint32 nUsing;                       /* 最终可使用的陀螺个数 */
	siint32 nValid;                       /* 陀螺头数据有效个数 */
	siint32 nMark;                        /* 陀螺组分数 */
	unint32 flagBalance;                  /* 本组平衡方程状态标志 */
	unint32 flagBalancePr1;               /* 上组平衡方程状态标志 */
	unint32 bGyroUsing;                   /* 陀螺正在使用标志 */

    float64 mat33Using[3][3];             /* 使用陀螺的安装矩阵 */
    float64 wb0[3];                       /* 转到本体系下的角速度 */

    float64 bi[3];                        /* 本体系下的常漂 */

    float64 wb[3];                        /* 转到本体系下的角速度（扣除标定的常漂） */

    float64 pG[3];                        /* 陀螺角速度积分 */
} SGyro;
typedef struct TAG_ATTMANEUVER
{
	unint32 bDynmicTrackOld;/* 目标跟踪模式 */	
	unint32 bManuverStart;  /* 姿态机动开始 */
	unint32 bPoint2P;       /* 点对点标志 */
	unint32 bDirChoose;     /* 机动方向选择 */
	float64 wmanv[3];       /* 机动角速度 */
	float64 dwmanv[3];      /* 机动角速度导数 */
	float64 otherT[3];      /* 其他补偿力矩 */
	float64 forwardT[3];    /* 机动前馈补偿力矩 */

	float64 PHI;            /* 轴角 */
	float64 phiTarget;      /* 轴角 */
	float64 eulerAxis[3];   /* 欧拉轴 */
	float64 qbt[4];         /* 目标四元素 */
	float64 qe[4];          /* 相对目标的误差姿态四元数 */
	float64 qc[4];          /* 相对规划的误差姿态四元数 */

	float64 target[3];      /* 机动目标角 */
	float64 targetB[3];     /* 机动目标角偏置 */
	float64 Cpi[3][3];      /* 规划姿态矩阵 */
	siint32 cntGotTargetE;  /* 理论机动到位计数器 */
	siint32 cntOverReal;    /* 实际 */
	unint32 InvMvn;

	unint32 bPID_Pushed;    /* PID已切换标志 */
	float64 PID_Push[3][3]; /* 保存的三轴PID参数 */
	float64 Kp[3];          /* 保存各模式下的控制器参数 */
	float64 Ki[3];
	float64 Kd[3];
} SAttManeuver;
typedef struct TAG_MODE_MANAGE
{
	unint32 flgMode;         /* 当前的模式 */
	unint32 flgSubMode;      /* 当前的子模式 */

	unint32 flgModeCru;		 /* 重要数据恢复模式 */
	unint32 flgSubModeCru;	 /* 重要数据恢复子模式 */

	unint32 flgModeNext;     /* 即将转入的模式 */
	unint32 flgSubModeNext;  /* 即将转入的子模式 */

	unint32 flgModePre;      /* 前一个模式 */
	unint32 flgSubModePre;   /* 前一个方式 */

	unint32 bNeedSwitch;     /* 需要转模式 */
	unint32 bEnSwitch;       /* 使能转模式 */

	unint32 bModeSwitch;     /* 转模式标志 */

	llong64 cntMode;         /* 模式计数器 */
	llong64 cntSubMode;      /* 方式计数器 */
	llong64 cntPc;           /* 内部小程控计数器 */

} SModeManage;

/* --- 全局变量定义 --- */
unint32 _nullStatement = 0u;
SStsData mStsSelectData;
SStsData mStsGyroData;
SGyro mGyro;
SDss mDss;
SAttitude mAttitude;
SAttManeuver mAttManeuver;
SModeManage mModeManage;

/* --- 函数原型 --- */
void AttitudeSelectXY(void);
void VectA2B(float64 *ptrB, const float64 *ptrA, siint32 num);

#endif // IP_ATTITUDESELECTXY_H