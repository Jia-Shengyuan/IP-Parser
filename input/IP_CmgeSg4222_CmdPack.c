#include "IP_CmgeSg4222_CmdPack.h"

// =======================================================
// 函数实现
// =======================================================

#if 0 // Compile error: mCmgCtrlOut is undefined, and I have no idea what it is.

void CmgeSg4222_CmdPack(unint08 *cmdOut, unint32 idx)
{
    unint32 tmpid;
	unint32 tmpU;

	tmpid = (mCmgCtrlOut.cmdId >> (4*idx)) & 0xF;

	if (tmpid != 0)
	{
	    if (tmpid == 0x01)   /* 框架角速度控制指令指令 */
		{
			cmdOut[0] = 0xEC;

			tmpU = (unint32)((siint32)(mCmgCtrlOut.cmdFloat[idx] * RAD2DEG / 0.0000214576722));
			cmdOut[1] = UI32_HILO8(tmpU);
			cmdOut[2] = UI32_LOHI8(tmpU);
			cmdOut[3] = UI32_LOLO8(tmpU);
			cmdOut[4] = CheckSumAdd08(&cmdOut[0], 4);  /* 校验和 */
		}
		else if (tmpid == 0x02) /* 框架定角保持指令 */
		{
			cmdOut[0] = 0xED;

			/* 框架角打包 */
			tmpU = (unint32)((siint32)(mCmgCtrlOut.cmdFloat[idx] * RAD2DEG/ 0.00004291534));
			cmdOut[1] = UI32_HILO8(tmpU);
			cmdOut[2] = UI32_LOHI8(tmpU);
			cmdOut[3] = UI32_LOLO8(tmpU);
			cmdOut[4] = CheckSumAdd08(&cmdOut[0], 4);  /* 校验和 */
		}
		else if (tmpid == 0x03) /* 框架当前位置锁定指令 */
		{
			cmdOut[0] = 0xEA;
			cmdOut[1] = 0xEA;
			cmdOut[2] = 0xEA;
			cmdOut[3] = 0xEA;
			cmdOut[4] = 0xA8;
		}
		else if (tmpid == 0x04) /* CMG软复位指令 */
		{
			cmdOut[0] = 0xE6;
			cmdOut[1] = 0xE6;
			cmdOut[2] = 0xE6;
			cmdOut[3] = 0xE6;
			cmdOut[4] = 0x98;
		}
		else if (tmpid == 0x05) /* 高速转子启动指令 */
		{
			cmdOut[0] = 0xE8;
			cmdOut[1] = 0xE8;
			cmdOut[2] = 0xE8;
			cmdOut[3] = 0xE8;
			cmdOut[4] = 0xA0;
		}
		else if (tmpid == 0x06) /* 高速转子滑行指令 */
		{
			cmdOut[0] = 0xE1;
			cmdOut[1] = 0xE1;
			cmdOut[2] = 0xE1;
			cmdOut[3] = 0xE1;
			cmdOut[4] = 0x84;
		}
		else
		{
			if (tmpid == 0x07) /* 高速转子转速设置指令 */
			{
				cmdOut[0] = 0xE2;

				/* 框架角打包 */
				tmpU = (unint32)((siint32)(mCmgCtrlOut.cmdFloat[idx] / 0.0014305));
				cmdOut[1] = UI32_HILO8(tmpU);
				cmdOut[2] = UI32_LOHI8(tmpU);
				cmdOut[3] = UI32_LOLO8(tmpU);
				cmdOut[4] = CheckSumAdd08(&cmdOut[0], 4);  /* 校验和 */
			}
		}
	}
	else
	{
	    cmdOut[0] = 0;
	    cmdOut[1] = 0;
	    cmdOut[2] = 0;
	    cmdOut[3] = 0;
	    cmdOut[4] = 0;
	}
}

#endif