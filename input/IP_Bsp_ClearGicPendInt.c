#include "IP_Bsp_ClearGicPendInt.h"

// =======================================================
// 函数实现
// =======================================================

void Bsp_ClearGicPendInt(U32 isrNo)
{
	U32 i,m=0;
	V_U32 *mec = (V_U32 *)(BSP_GIC_ICD_BASEADDR);
	U32 itlinesNumber;

	if(isrNo == ALL_USR_ISR)
	{
		itlinesNumber = (mec[BSP_INTR_ICDICTR / 4] & 0x1f) + 1;/*计算有多少组interrupt ID*/
		for(i = 0; i < itlinesNumber; i++)
		{
			mec[ (BSP_INTR_ICDICPR + i * 4) / 4] = 0xffffffff;/*清指定挂起中断*/
		}
	}
	else
	{
		/*清指定挂起中断*/
		m = isrNo / 32;
		mec[ (BSP_INTR_ICDICPR + (m * 4))/4 ] = (U32)(1 << (isrNo % 32));
	}

	return;
}