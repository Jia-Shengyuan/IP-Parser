#include "IP_CS_Sts_Gyro_Modify_Single.h"

// =======================================================
// 函数实现
// =======================================================

void StsCompensate(float64 *pSTSdeltaZ, const float64 *wGyro, const float64 *pSTSIV, float64 dtime)
{
    float64 tmpWm33[3][3];

    /* 根据惯性坐标系三轴姿态角速度得到时间偏差修正阵 */
    /* 输入参数wGyro对应星体三轴角速度 */
    tmpWm33[0][0] = 0.0;
    tmpWm33[0][1] =-wGyro[2];
    tmpWm33[0][2] = wGyro[1];

    tmpWm33[1][0] = wGyro[2];
    tmpWm33[1][1] = 0.0;
    tmpWm33[1][2] =-wGyro[0];

    tmpWm33[2][0] =-wGyro[1];
    tmpWm33[2][1] = wGyro[0];
    tmpWm33[2][2] = 0.0;

    /* 输入参数pSTSIV对应星敏标定后的安装矢量 */
    MatrixMulti(pSTSdeltaZ, &tmpWm33[0][0], pSTSIV, 3, 3, 1);

    /* 时间补偿量计算 */
    /* 输入参数dtime为星敏姿态对应时间到当前时刻的时间差 */
    /* 输出参数pSTSdeltaZ对应下文Imeasure_delta */
    pSTSdeltaZ[0] = pSTSdeltaZ[0] * dtime;
    pSTSdeltaZ[1] = pSTSdeltaZ[1] * dtime;
    pSTSdeltaZ[2] = pSTSdeltaZ[2] * dtime;

    return;
}

siint32 CS_GetKforSts(siint32 idx1, siint32 idx2)
{
    siint32 tmpNum1;
    siint32 tmpNum2;
    siint32 groupK;

    if (idx2 == -1) /* 单星敏 */
    {
        /* 单星敏时，其K阵组号即为星敏角标号 */
        groupK = idx1;
    }
    else /* 双星敏 */
    {
        /* K阵中单星敏组数以及双星敏组合组数构成递减等差数列
         * 单星敏组数为：NUM_STGR
         * 星敏idx1-1与其他星敏组合的组数为：NUM_STGR - idx1
         * 该等差数列的个数n为：单星敏、星敏0到星敏idx1-1与其他星敏的组合，即idx1 + 1
         * 因此K阵中双星敏组合（idx1，idx1 + 1）之前的组数和计算如下 */
        tmpNum1 = (idx1 + 1) * ((siint32)(NUM_SCOMPART_STGR) + (siint32)(NUM_SCOMPART_STGR)-idx1) / 2;

        /* K阵中双星敏组合（idx1，idx1 + 1）到（idx1，idx2）的组数为 */
        tmpNum2 = idx2 - idx1;

        /* K阵中组合（idx1，idx2）的组号（从零计，故有-1） */
        groupK = tmpNum1 + tmpNum2 - 1;
    }

    return groupK;
}

void StsModify(float64 *pdeltaZ, const float64 *pQ, const SSTSModifyData *pSTS1,
               const float64 *Gamma, float64 mdzmax)
{
    float64 tmpf;
    float64 tmpdZ;
    float64 tmpCq[3][3];
    float64 tmpZiGamma[3];
    float64 tmpV3a[3];
    float64 tmpV3b[3];
    float64 tmpV3c[3];
    float64 tmp33[3][3];

    float64 deltaX1[3];
    float64 deltaY1[3];
    float64 deltaZ1[3];

    /* 根据四元数计算方向余弦阵 */
    Q2C(&tmpCq[0][0], pQ);

    /* 星敏光轴测量值加光行差 */
    MatrixMulti(tmpV3a, &tmpCq[0][0], pSTS1->Imeasure[0], 3, 3, 1);

    /* Z ・ XT */
    MatrixMulti(&tmp33[0][0], &pSTS1->installVector1[2][0], &pSTS1->installVector1[0][0], 3, 1, 3);

    /* q2dcm(q) ・ γ */
    MatrixMulti(&tmpV3b[0], &tmpCq[0][0], Gamma, 3, 3, 1);

    MatrixMulti(&tmpV3c[0], &tmp33[0][0], &tmpV3b[0], 3, 3, 1);

    MatrixSub(tmpV3a, tmpV3a, tmpV3c, 3, 1);
    MatrixAdd(tmpV3a, tmpV3a, pSTS1->Imeasure_delta[0], 3, 1);
    VectorCross3(deltaX1, pSTS1->installVector1[0], tmpV3a);


    MatrixMulti(tmpV3a, &tmpCq[0][0], pSTS1->Imeasure[1], 3, 3, 1);

    /* Z ・ YT */
    MatrixMulti(&tmp33[0][0], &pSTS1->installVector1[2][0], &pSTS1->installVector1[1][0], 3, 1, 3);

    /* q2dcm(q) ・ γ  已在前面计算出来放在tmpV3b中了 */

    MatrixMulti(&tmpV3c[0], &tmp33[0][0], &tmpV3b[0], 3, 3, 1);

    MatrixSub(tmpV3a, tmpV3a, tmpV3c, 3, 1);
    MatrixAdd(tmpV3a, tmpV3a, pSTS1->Imeasure_delta[1], 3, 1);
    VectorCross3(deltaY1, pSTS1->installVector1[1], tmpV3a);


    MatrixAdd(tmpZiGamma, pSTS1->Imeasure[2], Gamma, 3, 1);
    MatrixMulti(tmpV3a, &tmpCq[0][0], tmpZiGamma, 3, 3, 1);
    MatrixAdd(tmpV3a, tmpV3a, pSTS1->Imeasure_delta[2], 3, 1);
    VectorCross3(deltaZ1, pSTS1->installVector1[2], tmpV3a);

    /* 修正新息pdeltaZ */
    MatrixAdd(pdeltaZ, deltaX1, deltaY1, 3, 1);
    MatrixAdd(pdeltaZ, pdeltaZ, deltaZ1, 3, 1);

    MatrixMultiScalar(pdeltaZ, pdeltaZ, 0.5, 3, 1);

    /* 新增 */
    tmpdZ = TripleFabsMax(pdeltaZ[0],pdeltaZ[1],pdeltaZ[2]);
    if(tmpdZ > mdzmax)
    {
        tmpf = mdzmax / tmpdZ;
        pdeltaZ[0] = tmpf * pdeltaZ[0];
        pdeltaZ[1] = tmpf * pdeltaZ[1];
        pdeltaZ[2] = tmpf * pdeltaZ[2];
    }

    return;
}

void StsFilter(float64 *bi_or_w, float64 *pQ, const float64 *pdeltaZ,
               const float64 *KS, const float64 mblimit)
{
    unint32 i;

    float64 tmpqb6[6];
    float64 tmpEq[4][3];
    float64 tmpQ[4];

    /* dq=tmpqb6{[0], [1], [2]},表示四元数的新息 */
    MatrixMulti(tmpqb6, KS, pdeltaZ, 6, 3, 1);

    /* 计算Eq(q) */
    Q2Ksi(&tmpEq[0][0], pQ);

    /* 计算Eq(q)×dq,只用tmpqb6的前3个元素 */
    MatrixMulti(tmpQ, &tmpEq[0][0], tmpqb6, 4, 3, 1);

    /* 姿态四元数 */
    for(i = 0; i < 4; i++)
    {
        pQ[i] = pQ[i] + tmpQ[i];
    }

    /* 对q进行归一化 */
    QUnit(pQ);

    /* 有陀螺时,返回值bi_or_w为星敏标定的陀螺漂移bi */
    /* 无陀螺时,返回值bi_or_w为计算的角速度w */
    for(i = 0; i < 3; i++)
    {
        bi_or_w[i] = bi_or_w[i] + tmpqb6[i + 3];
        bi_or_w[i] = LimitDouble(bi_or_w[i], mblimit);
    }


    return;
}

void CS_Sts_Gyro_Modify_Single(const unint32 num, unint32 cab)
{
    float64 t_gamma[3] = {0.0, 0.0, 0.0};
    float64 tmpKS[6][3];                      /* 滤波系数 */
    SSTSModifyData mSTSM;
    siint32 group;

    group = CS_GetKforSts((siint32)num, -1);

	Memcpyx((unint08 *)&mSTSM.installVector1[0][0], (unint08 *) &csStsParaC[cab].CbsT[num][0][0], sizeof(mSTSM.installVector1));

    /* XYZm对应Imeasure */
    Memcpyx((unint08 *)&mSTSM.Imeasure[0][0], (unint08 *) &csStsDataC[cab].XYZi_STG[num][0][0], sizeof(mSTSM.Imeasure));

    if (csStsCorrPara.F_STFilterPara[m_WorkMode] == 1)
    {
        /* 星敏陀螺定姿滤波系数(姿态机动模式) 单星敏 */
        Memcpyx((unint08 *)&tmpKS[0][0], (unint08 *)&csStsCorrPara.K_CorrMnv[cab][group][0][0], sizeof(tmpKS));
    }
    else
    {
        /* 星敏陀螺定姿滤波系数(正常模式) 单星敏 */
        Memcpyx((unint08 *)&tmpKS[0][0], (unint08 *)&csStsCorrPara.K_Corr[cab][group][0][0], sizeof(tmpKS));
    }

    /* 调用《基于单星敏感器测量矢量叉乘信息的滤波修正算法产品规范》 */
    /* void StsCompensate(float64 *pSTSdeltaZ, const float64 *wGyro, const float64 *pSTSIV, float64 dtime) */
    StsCompensate(&mSTSM.Imeasure_delta[0][0], &csAttCoreDataC[cab].w_STG[0], &mSTSM.installVector1[0][0], 0.0);
    StsCompensate(&mSTSM.Imeasure_delta[1][0], &csAttCoreDataC[cab].w_STG[0], &mSTSM.installVector1[1][0], 0.0);
    StsCompensate(&mSTSM.Imeasure_delta[2][0], &csAttCoreDataC[cab].w_STG[0], &mSTSM.installVector1[2][0], 0.0);

    /* void StsModify(float64 *pdeltaZ, const float64 *pQ, const SSTSModifyData *pSTS1,
                        const float64 *Gamma,float64 mdzmax) */
    StsModify(&csStsCorrDataC[cab].dInno_STG[0], &csAttCoreDataC[cab].q_STG[0], &mSTSM,
                &t_gamma[0], csStsCorrPara.Lmt_dInno[cab]);

    /* void StsFilter(float64 *bi_or_w, float64 *pQ, const float64 *pdeltaZ,
                        const float64 *KS, const float64 mblimit) */
    StsFilter(&csGyroDataC[cab].D0_STCorr[0], &csAttCoreDataC[cab].q_STG[0], &csStsCorrDataC[cab].dInno_STG[0],
                &tmpKS[0][0], csGyroParaW.Mlf_D0);

    return;
}