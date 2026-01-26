#include "IP_AttitudeSelectXY.h"

// =======================================================
// 函数实现
// =======================================================

void VectA2B(float64 *ptrB, const float64 *ptrA, siint32 num)
{

	siint32 si;

	for(si=0; si<num; si++)
	{
		ptrB[si] = ptrA[si];
	}

	return;
}

void AttitudeSelectXY(void)
{
    /* XY姿态数据选择 */

	/* 默认使用星敏陀螺的Cbi */
	/* Cbi、Cbr为星敏陀螺计算出来的 */
	VectA2B(&mAttitude.Cbi[0][0], &mStsGyroData.Cbi[0][0],3*3);
	VectA2B(&mAttitude.Cbo[0][0], &mStsGyroData.Cbo[0][0],3*3);
	VectA2B(&mAttitude.Cbr[0][0], &mStsGyroData.Cbr[0][0],3*3);

	if(mAttitude.flgXYIn == SI_KALMAN)
	{
		if (mGyro.bValid3Axis == TRUE32)
		{
			mAttitude.angle[0] = mStsGyroData.angle[0];
			mAttitude.angle[1] = mStsGyroData.angle[1];
#if HAVE_ES
			if (mKalman.flgAttSel != 0)
			{
				VectA2B(&mAttitude.Cbi[0][0], &mEsDssGyroAtt.Cbi_es[0][0], 3*3);
				VectA2B(&mAttitude.Cbr[0][0], &mEsDssGyroAtt.Cbr_es[0][0], 3*3);
				VectA2B(&mAttitude.Cbo[0][0], &mEsDssGyroAtt.Cbo_es[0][0], 3*3);
				mAttitude.angle[0] = mEsDssGyroAtt.angle[0];
				mAttitude.angle[1] = mEsDssGyroAtt.angle[1];
			}
#endif
		}
		else
		{
			mAttitude.angle[0] = mAttitude.angleB[0];
			mAttitude.angle[1] = mAttitude.angleB[1];
		}
	}
	else if(mAttitude.flgXYIn == SI_STS)  /* 用星敏数据 */
    {
		/* Cbi、Cbr为纯星敏计算出来的 */
		VectA2B(&mAttitude.Cbi[0][0], &mStsSelectData.Cbi[0][0],3*3);
		VectA2B(&mAttitude.Cbr[0][0], &mStsSelectData.Cbr[0][0],3*3);
		VectA2B(&mAttitude.Cbo[0][0], &mStsSelectData.Cbo[0][0],3*3);

        /* 星敏定姿 */
        if(mStsSelectData.bUsable == TRUE32)
        {
	        mAttitude.angle[0] = mStsSelectData.angle[0];
			mAttitude.angle[1] = mStsSelectData.angle[1];
        }
        else
		{
			mAttitude.angle[0] = mAttitude.angleB[0];
			mAttitude.angle[1] = mAttitude.angleB[1];
		}
    }
    else if(mAttitude.flgXYIn == SI_DSS)  /* 用数字太阳敏感器数据 */
	{
		if(mDss.bSpxy == FALSE32)
		{
			/* 太阳不可见 */
			mAttitude.angle[0] = mAttitude.angleB[0];
			mAttitude.angle[1] = mAttitude.angleB[1];
		}
		else
		{
			if(mModeManage.flgMode == SAM)
			{
				/* 太阳可见时 */
				mAttitude.angle[0] = mDss.angle[0];/* 转成变量 */
				mAttitude.angle[1] = mDss.angle[1];
			}
			else
			{
                mAttitude.angle[0] = mDss.angleSSF[0];
                mAttitude.angle[1] = mDss.angleSSF[1];
			}
		}
	}
	else if(mAttitude.flgXYIn == SI_RIGA) /* 用陀螺积分数据 */
	{
		mAttitude.angle[0] = mGyro.pG[0];
		mAttitude.angle[1] = mGyro.pG[1];
	}
#if HAVE_ES
	else if (mAttitude.flgXYIn == SI_ES)
	{
		/* 所有星敏不可用 */
		if (mSts.numUsable == 0)
		{
			/* 使用地敏的Cbi */
			VectA2B(&mAttitude.Cbi[0][0], &mEsDssGyroAtt.Cbi_es[0][0], 9);
			VectA2B(&mAttitude.Cbr[0][0], &mEsDssGyroAtt.Cbr_es[0][0], 9);
			VectA2B(&mAttitude.Cbo[0][0], &mEsDssGyroAtt.Cbo_es[0][0], 9);
		}

		if (mEsGr.bEPValid == TRUE32)
		{
			mAttitude.angle[0] = mEsGr.phi;
			mAttitude.angle[1] = mEsGr.theta;
		}
		else
		{
			mAttitude.angle[0] = mAttitude.angleB[0];
			mAttitude.angle[1] = mAttitude.angleB[1];
		}
	}
#endif
	else if(mAttitude.flgXYIn == SI_QUATERNION)
	{
		mAttitude.angle[0] = 2.0 * mAttManeuver.qc[0];
		mAttitude.angle[1] = 2.0 * mAttManeuver.qc[1];
	}
	else if(mAttitude.flgXYIn == SI_NO)  /* 不控 */
	{
		mAttitude.angle[0] = mAttitude.angleB[0];
		mAttitude.angle[1] = mAttitude.angleB[1];
	}
	else
	{
		NULL_STATEMENT();
	}

	C2Q(&mAttitude.qbi[0], &mAttitude.Cbi[0][0]);
	C2Q(&mAttitude.qbr[0], &mAttitude.Cbr[0][0]);

    return;
}