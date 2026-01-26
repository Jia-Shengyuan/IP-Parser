#ifndef IP_CS_STS_GYRO_MODIFY_SINGLE_H
#define IP_CS_STS_GYRO_MODIFY_SINGLE_H

#include <stdio.h> // 示例: 添加通用头文件

#include "common.h"

/* --- 类型定义 --- */
typedef double              float64;
typedef int                 siint32;
typedef struct TAG_STSMODIFY_DATA
{
    float64 installVector1[3][3];       /* 标定后的（如果有）三轴安装向量 */
    float64 installVector0[3][3];       /* 标称三轴安装向量 */

    float64 Imeasure[3][3];             /* 星敏的三轴测量值, 0:x轴,横轴 2:z轴,光轴 */
    float64 Imeasure_delta[3][3];       /* 星敏的三轴测量值的补偿值, 0:x轴,横轴 2:z轴,光轴 */

} SSTSModifyData;
typedef unsigned int        unint32;
typedef unsigned char       unint08;
typedef struct csAttCoreData_Type
{
    /* 星敏+陀螺 */
    float64 A_STG[3];                       /**< 星体三轴姿态(星敏+陀螺) */
    float64 Rate_STG[3];                    /**< 星体三轴姿态角速度(星敏+陀螺) */
    float64 q_STG[4];                       /**< 惯性姿态四元数(星敏) */
    float64 wbo_STG[3];                     /**< 星敏陀螺确定本体相对轨道系的惯性角速度 */
    float64 Cbo_STG[3][3];                  /**< 星敏陀螺估计的方向余弦阵 (从轨道坐标系到本体坐标系) */
    float64 w_STG[3];                       /**< 星体惯性角速度(星敏陀螺) [ωx_STG, ωy_STG, ωz_STG] */
    float64 wbiI_STG[3];                    /**< 星体惯性角速度在惯性系的表示(星敏有陀螺) */
    float64 wbiI_STG_Lst[NUM_STGRDELAY][3]; /**< 星体惯性角速度在惯性系的表示的历史值(星敏有陀螺) */

    float64 AttErr[3u]; /**< 节点舱i相对基准姿态的误差,单位rad */

    /* 星敏双矢量定姿 */
    float64 A_STDV[3];            /**< 星敏双矢量确定本体相对参考系的三轴姿态角 */
    /* float64 wbo_STDV[3]; */    /* 星敏双矢量确定本体相对轨道系的惯性角速度 */
    float64 Cbo_STDV[3][3];       /**< 星敏双矢量确定的方向余弦阵(从轨道坐标系到本体坐标系)*/
    float64 q_STDV[4];            /**< 星敏几何定姿四元数 */
    /* float64 q_STDV_Lst[4]; */  /* 星敏几何定姿四元数历史值 */
    /* float64 q_STGDV_Lst[4]; */ /* 星敏陀螺几何定姿四元数历史值 */

    unint32 AttFV;       /**< 节点舱i姿态有效性标志(0无效，1有效) AttCab[i].AttFV */
    unint32 WsFV;        /**< 节点舱角速度有效性标志 (0无效，1有效) AttCab[i].WsFV */
    unint32 FS_AttD_Lst; /**< 定姿方式历史值 */
} CS_ATT_CORE_DATA_T;
typedef struct csGyroWholePara_Type
{
    float64 Mlf_D0;                /**< 陀螺常值漂移限幅值,rad/h */
    float64 Mlf_De;                /**< 陀螺指数漂移限幅值,rad/h */
    float64 Mlfw;                  /**< 惯性角速度限幅,rad/s */
    unint32 FP_D0Update[NUM_WKMD]; /**< 陀螺常漂更新允许标志,1代表允许,0代表禁止 */
    unint32 NUM_GyrInEquation;     /**< 用于平衡方程遍历的陀螺个数 */
} CS_GYRO_WHOLE_PARA_T;
typedef struct csGyroData_Type
{
    float64 wbi[3];                           /**< 陀螺测量得到的星体三轴惯性角速度,单位为rad/s */
    float64 deltagm[NUM_SCOMPART_GYRGR];      /**< 陀螺i测量角度增量,Δgm,单位为rad/s */
    float64 deltag[3];                        /**< 陀螺测量得到的星体三轴输出,单位为rad */
    /* float64 De_ESCorr[3]; */               /**< 地敏估陀螺本体系三轴指数漂移项,单位为rad/h */
    /* float64 D0_ESCorr[3]; */               /**< 地敏估陀螺本体系三轴常值漂移,单位为rad/h */
    float64 D0_STCorr[3];                     /**< 星敏估陀螺本体系三轴常值漂移,单位为rad/h */
    float64 deltagm_Lst[NUM_SCOMPART_GYRGR];  /**< 陀螺i测量角度增量历史值,规范化算法接入接出,单位为rad/s */
    float64 deltag_Lst[3];                    /**< 陀螺测量得到的星体三轴输出 */
    unint32 FHV[NUM_SCOMPART_GYRGR];          /**< 陀螺i的硬件有效性标志(0:无效，1:有效)  */
    unint32 FS_Lst;                           /**< 陀螺i选取标志历史值(0,不引入;1,引入) */
} CS_GYRO_DATA_T;
typedef struct csStsCabinPara_Type
{
    float64 Cbs0T[NUM_SCOMPART_STGR][3][3]; /**< 星敏感器i的安装矩阵 */
    float64 CbsT[NUM_SCOMPART_STGR][3][3];  /**< (安装偏差补偿后的)星敏感器安装矩阵使用值,初值与Cbs0T相同 */
    unint32 FP_STCalbtComps;                /**< 星敏标定引入指令(0:引入，1:不引入) */
    unint32 FP_STCalbtUpdate;               /**< 是否用在轨标定结果重置星敏初始安装矩阵,1代表是 */
    unint32 FS;                             /**< 星敏i选取标志(0,不引入;1,引入),Dn~D0表示星敏n+1到星敏1 */
    unint32 FS_STOnBoardCalbt;              /**< 星敏在轨标定开关指令,0<=i<=NUM_STGR-1时引入星敏i为基准在轨标定;=NUM_STGR时取消星敏在轨标定,标定结果清零;=NUM_STGR+1时停止星敏在轨标定,标定结果不清零 */
} CS_STS_CABIN_PARA_T;
typedef struct csStsCabinData_Type
{
    float64 qm[NUM_SCOMPART_STGR][4];            /**< 未补偿的当前控制周期星敏感器i测量的姿态四元数 */
    float64 tm[NUM_SCOMPART_STGR];               /**< 未补偿的星敏感器i测量时刻对应的星时,曝光时间,单位为s */
    float64 dt[NUM_SCOMPART_STGR];               /**< 星敏i的测量时刻与使用时刻之间的时延,Δt,单位为s */
    float64 dbeta[NUM_SCOMPART_STGR][3];         /**< 星敏i光行差修正量,Δβ */
    float64 v[NUM_SCOMPART_STGR][3];             /**< 星敏i光行差相对速度,单位为km/s */
    float64 t[NUM_SCOMPART_STGR];                /**< 补偿后的星敏感器i测量时刻对应的星时,单位为s */
    float64 XYZm[NUM_SCOMPART_STGR][3][3];       /**< 未补偿的星敏感器i的测量X轴、Y轴和Z轴在惯性系中的方位 */
    float64 XYZm_Lst[NUM_SCOMPART_STGR][3][3];   /**< 未补偿的星敏感器i的测量X轴、Y轴和Z轴在惯性系中的方位历史值 */
    float64 XYZi_STG[NUM_SCOMPART_STGR][3][3];   /**< 星敏时间和光行差补偿后的X轴、Y轴和Z轴输出(星敏有陀螺),Xi_STG/Yi_STG/Zi_STG */
    float64 XYZi_STDyn[NUM_SCOMPART_STGR][3][3]; /**< 星敏时间和光行差补偿后的X轴、Y轴和Z轴输出(星敏无陀螺),Xi_STDyn/Yi_STDyn/Zi_STDyn */
    /* 星敏遥测数据计算 */
    float64 Xm_YC[NUM_SCOMPART_STGR][3];                      /**< 星敏感器i的测量X轴在惯性系中的方位,遥测计算用 */
    float64 Ym_YC[NUM_SCOMPART_STGR][3];                      /**< 星敏感器i的测量Y轴在惯性系中的方位,遥测计算用 */
    float64 Zm_YC[NUM_SCOMPART_STGR][3];                      /**< 星敏感器i的测量Z轴在惯性系中的方位,遥测计算用 */
    float64 A[NUM_SCOMPART_STGR][3];                          /**< 星敏i计算的三轴姿态角,遥测,φ/θ/ψ,单位为rad */
    float64 alpha_ZiSun[NUM_SCOMPART_STGR];                   /**< 星敏的光轴与太阳矢量夹角,α_ZiSun,单位为rad */
    float64 alpha_ZiEarth[NUM_SCOMPART_STGR];                 /**< 星敏的光轴与地心矢量夹角,α_ZiEarth,单位为rad */
    float64 dAlpha_STz[NUM_SCOMPART_STGR][NUM_SCOMPART_STGR]; /**< 两星敏光轴夹角与标称角的误差,Δα_STz[i][j],单位为角秒 */
    float64 dAlpha_STx[NUM_SCOMPART_STGR][NUM_SCOMPART_STGR]; /**< 两星敏横轴夹角与标称角的误差,Δα_STx[i][j],单位为角秒 */
    float64 dAlpha_STy[NUM_SCOMPART_STGR][NUM_SCOMPART_STGR]; /**< 两星敏横轴夹角与标称角的误差,Δα_STy[i][j],单位为角秒 */
    /* 星敏标定 */
    float64 dAlpha_Cbs_Cali[NUM_SCOMPART_STGR][3]; /**< 星敏i相对基准星敏的相对安装误差角,Δα_Cbs_Cali,单位为rad */
    unint32 FHV[NUM_SCOMPART_STGR];                /**< 星敏感器i的硬件有效性标志,0代表无效,1代表有效 */
    unint32 F_STGCatch;                            /**< 星敏陀螺定姿机动到位后星敏是否有效标志,0代表机动到稳态模式后星敏无有效姿态,1代表机动到稳态模式后星敏输出有效姿态 */
} CS_STS_C_DATA_T;
typedef struct csStsCorrPara_Type
{
    /* 星敏陀螺滤波系数 */
    float64 K_Corr[NUM_COMPART][GROUPS_STS_K_CORR][6][3];    /**< 星敏陀螺定姿滤波系数(正常模式),星敏有陀螺[AB/AC/BC],双星敏[0-2]单星敏[3-5] */
    float64 K_CorrMnv[NUM_COMPART][GROUPS_STS_K_CORR][6][3]; /**< 星敏陀螺定姿滤波系数(姿态机动模式),双星敏[AB/AC/BC],双星敏[0-2]单星敏[3-5] */
    /* 星敏修正系数 */
    float64 MlfA_ST[3];                /**< 姿态估计的角度限幅阈值,Mlfφ_ST/Mlfθ_ST/Mlfψ_ST,单位为rad */
    float64 MlfAlpha_STCali;           /**< 星敏安装偏差角度限幅,Mlfα_STCali,单位为rad */
    float64 MlfdPhiDelay[NUM_COMPART]; /**< 星敏时间补偿的误差角度限幅,MlfΔΦDelay,单位为rad */
    float64 Mdf_f_STCali;              /**< 星敏基准标定的123转序三轴误差角滤波系数 */
    float64 Mlfw_STDyn;                /**< 星敏无陀螺修正的角速度限幅,单位为rad/s */
    float64 Lmtdg_Zero;                /**< 姿态四元数除零保护阈值 */
    float64 Lmt_dInno[NUM_COMPART];    /**< 星敏修正残差超差则限幅的阈值,Lmt_ΔInno,单位为rad */
    /* 星敏双矢量定姿系数 */
    float64 Lmtdq_STDV;   /**< 星敏双矢量姿态捕获成功判定阈值,LmtΔq_STDV */
    float64 Lmtdq_qReset; /**< 重置四元数时的四元数误差判断阈值,LmtΔq_qReset */
    float64 dt0_qReset;   /**< 四元数重置的时间范围,Δt0_qReset,单位为s */
    float64 dt1_qReset;   /**< 四元数重置的时间范围,Δt1_qReset,单位为s */
    /* 星敏定姿相关标志 */
    unint32 FP_STAttKFin;             /**< 姿态保持模式星敏修正允许,0代表不允许,1:代表允许 */
    unint32 F_STFilterPara[NUM_WKMD]; /**< 星敏滤波系数选择标志,1时选取为机动条件下的滤波系数,否则为正常系数 */
    unint32 FP_qReset;                /**< 机动到位后q重置允许标志,0代表不允许,1代表允许 */
    unint32 FS_qInit_AttChg;          /**< 定姿切换时四元数赋初值,0代表标称本体系相对惯性姿态赋初值,1代表当前本体系相对惯性姿态赋初值 */
    unint32 LmtN_dq_STDV;             /**< 星敏全天球捕获成功连续满足次数 */
} CS_STS_CORR_PARA_T;
typedef struct csStsCorrCabinData_Type
{
    float64 q_STDV_Lst[4]; /**< 星敏几何定姿四元数,历史值 */
    /* 星敏修正 */
    float64 dInno_STG[3]; /**< 星敏陀螺定姿的限幅后新息修正量,ΔInno_STG,单位为rad */
    /* 星敏无陀螺动力学 */
    float64 ad[3]; /**< 计算星体加速度[dωx; dωy; dωz],单位为rad/s^2 */
    /* 双矢量 */
    float64 qm_Coarse[NUM_SCOMPART_STGR][4]; /**< 星敏i粗姿态 */
    float64 wm_coarse[NUM_SCOMPART_STGR][4]; /**< 星敏i粗姿态角速度,rad/s */
    float64 t_q_STDV_Lst;                    /**< 星敏几何定姿时标历史值 */
    float64 t_q_STGDV_Lst;                   /**< 星敏陀螺定姿的星敏几何定姿时标历史值 */
    unint32 FV_STDV;                         /**< 星敏双矢量定姿有效标志,0代表无效,1代表有效 */
    unint32 Cnt_dq_STGDV;                    /**< 星敏陀螺几何定姿连续成功次数 */
} CS_STS_CORR_C_DATA_T;

/* --- 全局变量定义 --- */
CS_ATT_CORE_DATA_T csAttCoreDataC[NUM_COMPART];
CS_GYRO_WHOLE_PARA_T csGyroParaW;
CS_GYRO_DATA_T csGyroDataC[NUM_COMPART];
CS_STS_CORR_PARA_T csStsCorrPara;
CS_STS_CABIN_PARA_T csStsParaC[NUM_COMPART];
CS_STS_C_DATA_T csStsDataC[NUM_COMPART];
CS_STS_CORR_C_DATA_T csStsCorrDataC[NUM_COMPART];
unint32 m_WorkMode;

/* --- 函数原型 --- */
siint32 CS_GetKforSts(siint32 idx1, siint32 idx2);
void CS_Sts_Gyro_Modify_Single(const unint32 num, unint32 cab);
void StsCompensate(float64 *pSTSdeltaZ, const float64 *wGyro, const float64 *pSTSIV, float64 dtime);
void StsFilter(float64 *bi_or_w, float64 *pQ, const float64 *pdeltaZ,
               const float64 *KS, const float64 mblimit);
void StsModify(float64 *pdeltaZ, const float64 *pQ, const SSTSModifyData *pSTS1,
               const float64 *Gamma, float64 mdzmax);

#endif // IP_CS_STS_GYRO_MODIFY_SINGLE_H