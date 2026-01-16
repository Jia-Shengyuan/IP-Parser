#ifndef IP_INPUTPROCEED_H
#define IP_INPUTPROCEED_H

#include <stdio.h> // 示例: 添加通用头文件

#include "common.h"

/* --- 类型定义 --- */
typedef unsigned char   unint08;
typedef float           float32;
typedef unsigned int    unint16;
typedef unsigned long   unint32;
typedef struct TAG_DIGITAL_GYRO_DATA
{

    unint08		countPick[9];		 	/* 陀螺原始数据处理时,剔野计数器 */   
    float32 	Gi[3];				 	/* 陀螺角度积分 */
    float32 	wa[9];				 	/* 陀螺角速度模拟 */
    float32 	wal[9];				 	/* 上周期陀螺角速度模拟量 */
 	unint08		JoinTotal;           	/* 参加定姿的陀螺个数 */
 	unint16 	gyroStatus0;		 	/* 陀螺状态旧 */
 	unint16 	gyroStatus1;		 	/* 陀螺状态新 */
    float32 	W[3];				 	/* 陀螺算出的角速度 */
    unint08		SignFlag[9] ; 		 	/* 参加定姿的陀螺序号 */    
	float32 	Rtemp[3][5];		 	/* 矩阵计算结果 */
	unint32		stateFlag[9];			/* 陀螺加电状态 */
	
} SGyroData;
typedef signed   char   siint08;
typedef struct TAG_ATTITUDE_PARA     	
{                                    	
	                                 	
	float32 	angle[3];			 	/* 三轴姿态角 */
	float32 	rate[3]; 			 	/* 三轴角速度 */
	                                 	
}SAttitude;
typedef struct TAG_DSS_DATA
{	
	unint32     stateFlag_A;			/* 主份加电 */
	unint32     stateFlag_B;			/* 备份加电 */
	float32 	royaw;
	float32 	piyaw;
    unint32     flgSP;					/* 太阳可见标志 */
}SDSSData;

/* --- 全局变量定义 --- */
volatile unint08		  		flgGryoCalc;
float32	VG[9][3] = { { 0.7672553f, -0.2792581f,  0.5773510f},
  						 {-0.1417830f, -0.8040916f,  0.5773510f},
  						 {-0.1417830f,  0.8040916f,  0.5773510f},
  						 { 0.7672553f,  0.2792581f,  0.5773510f},
  						 {-0.6254722f, -0.5248335f,  0.5773510f},
  						 {-0.6254722f,  0.5248335f,  0.5773510f},
  						 {-0.4082480f, -0.7071063f, -0.5773510f},
  						 {-0.4082480f,  0.7071063f, -0.5773510f},
  						 { 0.8164960f,  0.0f,       -0.5773510f}	};
SGyroData         				mGyroData;
SAttitude         				mAttitude;
SDSSData          				mDSSData;

/* --- 函数原型 --- */
void CalculateGyroDg( SGyroData *pGyroData );
void CalculateGyroRs(SGyroData *pGyroData);
void GyroChoose(SGyroData *pGyroData);
void GyroPick(SGyroData *pGyroData);
void GyroProceed(void);
void Inputproceed(void);
unint08 MatrixInv33F(float32 *inv, const float32 *src);
void MatrixMulti(float32 *product,
                 const float32 *faciend,
                 const float32 *multiplier,
                 unint08 nrow,
                 unint08 nrc,
                 unint08 ncol);
void MatrixTran(float32 *tran,
          const float32 *mat,
                unint08 nrow,
                unint08 ncol);
float32 ModPNHP(float32 x, float32 halfperiod);
unint08 Tr32Uint08(volatile unint08 *pA, volatile unint08  *pB, volatile unint08 *pC);

#endif // IP_INPUTPROCEED_H