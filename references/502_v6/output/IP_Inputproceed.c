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

// =======================================================
// 函数实现
// =======================================================

void MatrixMulti(float32 *product,
                 const float32 *faciend,
                 const float32 *multiplier,
                 unint08 nrow,
                 unint08 nrc,
                 unint08 ncol)
{
    unint08 ir ;			                                /* 行循环变量 */
    unint08 jc ;			                                /* 列循环变量 */
    unint08 nk ;			                                /* 求积后做加个数 */
    unint08 index ;			                                /* 矩阵计算结果位置 */

    /* product:求和结果矩阵指针 */
    /* faciend:求和矩阵 */
    /* multiplier:被求和矩阵 */
    /* nrow:矩阵行数 */
    /* nrc:求积后做加个数 */
    /* ncol:矩阵列数 */

    for (ir=0 ; ir<nrow ; ir++)                             /* 行循环 */
    {
        for (jc=0 ; jc<ncol ; jc++)                         /* 列循环 */
        {
            index = ir * ncol + jc ;		                /* 矩阵计算结果位置 */

            product[index] = 0.0f ;			                /* 乘积结果默认取0 */

            for (nk=0 ; nk<nrc ; nk++)                      /* 求积后做加个数循环 */
            {
                product[index] = product[index] + faciend[ir * nrc + nk] * multiplier[nk * ncol + jc] ;
            }
        }
    }

    return ;
}

void CalculateGyroDg( SGyroData *pGyroData )
{
 	unint08 j ;
	unint08 k ;
	float32 tmpwa[5] ;

	for (j = 0 ; j < 5 ; j++ )	                            /* 给临时数组赋值 */
	{
	     tmpwa[j] = 0 ; 									/* 赋值为0，使用时修改 */
    }
	for ( j=0 ; j < pGyroData->JoinTotal ; j++ )
	{
		k = pGyroData->SignFlag[j] ;							/* 所有参加诊断陀螺的序号 */
		tmpwa[j] = pGyroData->wa[k] ;						/* 取对应序号的模拟量测量值 */
	}

	if ( pGyroData->JoinTotal >= 3 )							/* 若大于三个陀螺工作可定姿 */
	{
		                                                    /* 算角速度 */
		MatrixMulti(&(pGyroData->W[0]), &(pGyroData->Rtemp[0][0]), &tmpwa[0], 3, 5, 1) ;

	}
	else
	{
		pGyroData->W[0] = 0.0f ;								/* 参加定姿的陀螺太少 */
		pGyroData->W[1] = 0.0f ;
		pGyroData->W[2] = 0.0f ;
	}

	return ;
}

void GyroPick(SGyroData *pGyroData)
{
    unint08 iy ;
    float32 tmpgi ;

    for ( iy = 0 ; iy < 9 ; iy++ )
    {

        tmpgi = ABS(pGyroData->wa[iy] - pGyroData->wal[iy]) ;	/* 角度增量剔野处理 */

        if (tmpgi > 0.048f)    								/* 剔野限0.048°/s */
        {
            pGyroData->countPick[iy]++ ;						/* 野值计数器 */

            if (pGyroData->countPick[iy] < 6)   				/* 没有6次连续野值 */
            {
                pGyroData->wa[iy] = pGyroData->wal[iy] ;		/* 用上周期的值代替本周期的值 */

            }
            else                                			/* 连续6周期野值 */
            {
                pGyroData->wal[iy] = pGyroData->wa[iy] ;		/* 用本周期的值代替上周期的值 */

                pGyroData->countPick[iy] = 0 ;				/* 替代后，野值计数器清零 */

            }
        }
        else                     							/* 没有超出剔野限 */
        {
            pGyroData->wal[iy] = pGyroData->wa[iy] ;			/* 用新值 */

            pGyroData->countPick[iy] = 0 ;					/* 野值计数器清零 */

        }
    }

    return ;

}

void GyroChoose(SGyroData *pGyroData)
{
	unint08 i ;									      		/* 循环用临时变量 */

	/* 确定参加工作陀螺的个数 */
	pGyroData->JoinTotal = 0 ;								/* 参加定姿的陀螺个数清零 */
	pGyroData->gyroStatus0 = 0 ;

	for ( i=0 ; i<9 ; i++ )									/* 9个陀螺进行判断 */
	{
		if (pGyroData->stateFlag[i] == TRUE)  				/* 如果陀螺状态正常 */
		{
			pGyroData->SignFlag[pGyroData->JoinTotal] = i ;	/* 统计参加定姿的陀螺螺序号 */
			pGyroData->JoinTotal++ ;							/* 统计参加定姿的陀螺个数 */
			pGyroData->gyroStatus0 = pGyroData->gyroStatus0 | (1 << i) ;
		}

	}

	return ;
}

float32 ModPNHP(float32 x, float32 halfperiod)
{
    float32 period;                                         /* 周期 */
    float32 npp2;                                           /* 限幅后的返回值 */

    /* 计算周期值 */
    period = 2.0f * halfperiod;

    npp2 = x - floor((x + halfperiod) / period) * period;   /* 限幅并返回 */

    return npp2;
    }

void MatrixTran(float32 *tran,
          const float32 *mat,
                unint08 nrow,
                unint08 ncol)
{
	/* 注意源和目标矩阵/向量不能是同一个 */
    unint08 i ;		/* 矩阵行循环变量 */
    unint08 j ;		/* 矩阵列循环变量 */

   /* tran:目标矩阵 */
   /* mat: 源矩阵 */
   /* nrow:矩阵行数 */
   /* ncol:矩阵列数 */

    for ( i=0 ; i<nrow ; i++ )                              /* 行循环 */
    {
        for ( j=0 ; j<ncol ; j++ )                          /* 列循环 */
        {
            *(tran + j * nrow + i) = *(mat + i * ncol + j) ;
        }
    }

    return ;
}

unint08 MatrixInv33F(float32 *inv, const float32 *src)
{
    siint08 i;
    float32 rank;
    unint08 bAbleInv;   /* TRUE32:矩阵可逆 */

    /* inv:输出结果矩阵指针 */
    /* src:输如计算矩阵指针 */

    /* 默认不可逆 */
    bAbleInv = FALSE32;

    inv[0] = src[4] * src[8] - src[5] * src[7];             /* 第1行第1列 */
    inv[1] = src[2] * src[7] - src[1] * src[8];             /* 第1行第2列 */
    inv[2] = src[1] * src[5] - src[2] * src[4];             /* 第1行第3列 */
    inv[3] = src[5] * src[6] - src[3] * src[8];             /* 第2行第1列 */
    inv[4] = src[0] * src[8] - src[2] * src[6];             /* 第2行第2列 */
    inv[5] = src[2] * src[3] - src[0] * src[5];             /* 第2行第3列 */
    inv[6] = src[3] * src[7] - src[4] * src[6];             /* 第3行第1列 */
    inv[7] = src[1] * src[6] - src[0] * src[7];             /* 第3行第2列 */
    inv[8] = src[0] * src[4] - src[1] * src[3];             /* 第3行第3列 */

    /* 求矩阵的行列式值 */
    rank = src[0] * inv[0] + src[1] * inv[3] + src[2] * inv[6];


    if ((FLT32_ZERO < rank) || (rank < -FLT32_ZERO))         /* 不等于浮点数0 */
    {

        bAbleInv = TRUE32;                                   /* 矩阵可逆 */

        for (i=0; i<9; i++)                                  /* 行列式 */
        {
            inv[i] = inv[i] / rank;
        }
    }
    else
    {
        /* 矩阵不可逆时与原矩阵一致 */
        for (i=0; i<9; i++)
        {
            inv[i] = src[i];
        }
    }

    return bAbleInv;
}

void CalculateGyroRs(SGyroData *pGyroData)
{
	unint08 i ;
 	unint08 j ;
	unint08 k ;
 	float32 Rgtrans[3][5] ;
 	float32 Rs[3][3] ;
	float32 RsInv[3][3] ;
 	float32 Rgtemp[5][3] ;

 	pGyroData->JoinTotal = MIN(pGyroData->JoinTotal, 5) ;

	if (pGyroData->gyroStatus0 != pGyroData->gyroStatus1)		/* 有陀螺切换 */
	{
		flgGryoCalc = TRUE ;								/* 置陀螺计算标志 */

		for ( j = 0 ; j < pGyroData->JoinTotal ; j++ )			/* 参加定姿的陀螺个数 */
		{
			k = pGyroData->SignFlag[j] ;						/* 按从小到大排列依次选5个，不足5个选余下的 */

			for ( i=0 ;  i<3 ; i++ )
			{
				Rgtemp[j][i] = VG[k][i] ;					/* n*3的安装阵R */
			}
		}

		for ( i = pGyroData->JoinTotal ; i<5 ; i++ )			/* 不用的（5-JoinTotal）维，清零 */
		{
			for ( j=0 ; j<3 ; j++ )
			{
				Rgtemp[i][j] = 0.0f;
			}
		}

		if (pGyroData->JoinTotal >= 3)						/* 若大于三个陀螺工作可以计算角速度 */
		{

			MatrixTran(&Rgtrans[0][0], &Rgtemp[0][0], 5, 3) ;					/* Rg->Rgtrans    		*/
			MatrixMulti(&Rs[0][0], &Rgtrans[0][0], &Rgtemp[0][0], 3, 5, 3) ;	/* R*RT->RS       		*/
			MatrixInv33F(&RsInv[0][0], &Rs[0][0]) ;								/* INV(RS)->RsInv 		*/
			MatrixMulti(&(pGyroData->Rtemp[0][0]), &RsInv[0][0], &Rgtrans[0][0], 3, 3, 5) ;	/* RsInv*Rgtrans->Rtemp */
		}

		pGyroData->gyroStatus1 = pGyroData->gyroStatus0 ;
	}

	return ;
}

void GyroProceed(void)
{
    float32 dgi[2] ;

    GyroPick(&mGyroData) ;										    /*  B1：剔野 */

    /* B2：计算三轴角速度 */
    GyroChoose(&mGyroData) ;											/* 陀螺选择 */
	CalculateGyroRs(&mGyroData) ;
    CalculateGyroDg(&mGyroData) ;										/* 陀螺三轴角速度计算 */

    /* SAM不进行陀螺漂移补偿 */
    dgi[0] = mGyroData.Gi[0] + mGyroData.W[0] * 0.160f ;	/* 控制周期0.16 */
    dgi[1] = mGyroData.Gi[1] + mGyroData.W[1] * 0.160f ;	/* 控制周期0.16 */

    /* 陀螺角度积分,限在(-180, 180)之间 */
    mGyroData.Gi[0] = ModPNHP(dgi[0], 180.0f) ;				/* 滚动角积分 = 上周期积分总值 + 本周期积分改变值 */
    mGyroData.Gi[1] = ModPNHP(dgi[1], 180.0f) ;			    /* 滚动角积分 = 上周期积分总值 + 本周期积分改变值 */

    return ;
}

unint08 Tr32Uint08(volatile unint08 *pA, volatile unint08  *pB, volatile unint08 *pC)
{
    unint08 uitemp1 ;
    unint08 uitemp2 ;
    unint08 uitemp3 ;
    unint08 uiresult ;

    if (((*pA) == (*pB)) && ((*pA) == (*pC)))
    {
        uiresult = (*pA) ;
    }
    else
    {
        uitemp1 = (*pA) & (*pB) ;
        uitemp2 = (*pA) & (*pC) ;
        uitemp3 = (*pB) & (*pC) ;
        uiresult = uitemp1 | uitemp2 | uitemp3 ;

        *pA = uiresult ;
        *pB = uiresult ;
        *pC = uiresult ;
    }

    return uiresult ;
}

void Inputproceed(void)
{
	unint08 flgSP ;											/* 硬口读入SP标志 */
    unint08 flgModetmp ;									/* 模式字 */

    flgModetmp = TR32_FLGMODE() ;							/* 方式字 */

	GyroProceed() ;											/* 陀螺数据处理 */
	
	if ( flgModetmp == SAM_CRUISE )     					/* 巡航方式 */
	{
		if ( mDSSData.flgSP == 1 )   						/* 太阳可见 */
		{
        	mAttitude.angle[0] = mDSSData.royaw ;			/* 滚动角用太敏 */
        	mAttitude.angle[1] = mDSSData.piyaw ;			/* 俯仰角用太敏 */

        	 												/* 将太敏读数替换当前积分值 */
       		mGyroData.Gi[0] = mDSSData.royaw ;				/* 滚动角陀螺积分  */
       		mGyroData.Gi[1] = mDSSData.piyaw ;				/* 俯仰角陀螺积分  */
		}
		else												/* 太阳不可见 */
		{
		    mAttitude.angle[0] = mGyroData.Gi[0] ;			/* 滚动角用陀螺积分 */
        	mAttitude.angle[1] = mGyroData.Gi[1] ;			/* 俯仰角用陀螺积分 */
		}
	}

	else    /* 其他模式 */
	{
		mAttitude.angle[0] = 0.0f ;							/* 滚动角清零 */
    	mAttitude.angle[1] = 0.0f ;							/* 俯仰角清零 */
	}


	mAttitude.rate[0] = mGyroData.W[0] ;					/* 滚动角速度用陀螺算出的滚动角速度 */
    mAttitude.rate[1] = mGyroData.W[1] ;					/* 俯仰角速度用陀螺算出的俯仰角速度 */
	mAttitude.rate[2] = mGyroData.W[2] ;					/* 偏航角速度用陀螺算出的偏航角速度 */


	return ;
}