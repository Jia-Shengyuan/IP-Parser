/**
 * @file common.h
 * @brief 自动提取的项目全局宏和枚举定义
 * @note 此文件由 create_common_h.py 脚本自动生成于 2025-11-13 11:04:46
 */

#ifndef AUTO_GENERATED_COMMON_H
#define AUTO_GENERATED_COMMON_H

/* --- 自动提取的宏定义 (MACROS) --- */

#define     ReadReg(Addr)                (ADDR_READ(Addr))


#define  FALSE32                    0x00  /* 返回布尔假定义 */


#define  FLT32_ZERO                 1.0E-6


#define  TRUE32                     0x90  /* 返回布尔真定义 */


#define ABS(a)                  	(((a) > 0) ? (a) : -(a))


#define ADDR_AD_START				0xA000		/* 读地址0xA000启动AD转换 */


#define ADDR_READ(addr)             (*((volatile unsigned int *)(addr)))


#define ADDR_STATE				    0xE000		/* SP */


#define ADDR_WRITE(addr, value)     {(*((volatile unsigned int *)(addr))) = (value);}


#define AD_SS_GYRO_HI8				0xA001		/* A/D转换后的12位数据,0xA001的D[7:0]（高8位） */


#define AD_SS_GYRO_LO4				0xA003		/* A/D转换后的12位数据,0xA003的D[7:4]（低4位） */


#define DIVIATION_TO_FLOAT_DSS(x)	DiviationToFloat((x), 0xFFF, 0x800, 2.44140625e-3f)  /*  5/2048 -5~5° */


#define DIVIATION_TO_FLOAT_FOG(x)   DiviationToFloat((x), 0xFFF, 0x800, 9.765625e-4f)      /*    1/1024° */


#define DIVIATION_TO_FLOAT_GYRO(x)  DiviationToFloat((x), 0xFFF, 0x800, 1.62760417e-3f)    /*  5/3072 -2.5~2.5°/S  */


#define FALSE           			0x00


#define FST_BIAS_WXRO       		((volatile float *)0x7D18)


#define FST_BIAS_WYPI       		((volatile float *)0x7D1C)


#define FST_FLGMODE					((volatile unsigned char *)0x7D00)


#define FST_FT_HEALTHWORD      	    ((volatile unsigned int *)0x7D24)


#define MIN(a, b)                   (((a) > (b)) ? (b) : (a))


#define NOCTRL						0x44	/* 不控 */


#define PS_C000						0xC000		/* 太敏等电源状态 */


#define RAM_VALIDATE(addr)      ((0x0  <= (addr)) && ((addr) <= 0x7FFF))


#define SAM_CRUISE          		0x33	/* SAM巡航方式 */


#define SAM_DAMP            		0x00	/* SAM速率阻尼方式 */


#define SAM_PITCH           		0x11	/* SAM俯仰搜索方式 */


#define SAM_ROLL            		0x22	/* SAM滚动搜索方式 */


#define SND_BIAS_WXRO       		((volatile float *)0x7E6C)


#define SND_BIAS_WYPI       		((volatile float *)0x7E70)


#define SND_FLGMODE					((volatile unsigned char *)0x7E54)


#define SND_FT_HEALTHWORD       	((volatile unsigned int *)0x7E78)


#define TBS_A               		0x00     /* 选择A分支 */


#define TBS_AB              		0xCC     /* 选择AB分支 */


#define TBS_B               		0x33     /* 选择B分支 */


#define TR16_VALUE(pA,pB,pC,nval)   {*(pA) = (nval);    *(pB) = (nval);    *(pC) = (nval);}


#define TR32_BIAS_WXRO()			Tr32Float(FST_BIAS_WXRO, SND_BIAS_WXRO, TRD_BIAS_WXRO)


#define TR32_BIAS_WXRO_VALUE(x)		TR32_VALUE(FST_BIAS_WXRO, SND_BIAS_WXRO, TRD_BIAS_WXRO, (x))


#define TR32_BIAS_WYPI()			Tr32Float(FST_BIAS_WYPI, SND_BIAS_WYPI, TRD_BIAS_WYPI)


#define TR32_BIAS_WYPI_VALUE(x)		TR32_VALUE(FST_BIAS_WYPI, SND_BIAS_WYPI, TRD_BIAS_WYPI, (x))


#define TR32_FLGMODE()				Tr32Uint08(FST_FLGMODE, SND_FLGMODE, TRD_FLGMODE)


#define TR32_FLGMODE_VALUE(x)		TR32_VALUE(FST_FLGMODE, SND_FLGMODE, TRD_FLGMODE, (x))


#define TR32_FT_HEALTHWORD()		Tr32Uint(FST_FT_HEALTHWORD, SND_FT_HEALTHWORD, TRD_FT_HEALTHWORD)


#define TR32_VALUE(pA,pB,pC,nval)   {*(pA) = (nval);    *(pB) = (nval);    *(pC) = (nval);}


#define TRD_BIAS_WXRO       		((volatile float *)0x7FC0)


#define TRD_BIAS_WYPI       		((volatile float *)0x7FC4)


#define TRD_FLGMODE					((volatile unsigned char *)0x7FA8)


#define TRD_FT_HEALTHWORD       	((volatile unsigned int *)0x7FCC)


#define TRUE            			0xEB


#define UI16_HI8(ui16)                  (((ui16) >>  8) & MASK_LOLO_08)


#define UI16_LO8(ui16)                  (((ui16)      ) & MASK_LOLO_08)


#define UI32_HIHI8(ui32)                (((ui32) >> 24) & MASK_LOLO_08)


#define UI32_HILO8(ui32)                (((ui32) >> 16) & MASK_LOLO_08)


#define UI32_LOHI8(ui32)                (((ui32) >>  8) & MASK_LOLO_08)


#define UI32_LOLO8(ui32)                (((ui32)      ) & MASK_LOLO_08)


#define USCFR                    0x00C3 /* fifo复位寄存器 */


#define USCNTR3                  0x00D2 /* FIFO计数寄存器                                                     */


#define USDR3                    0x00D3 /* US数据寄存器 */


#define USDR5                    0x00DB /* US数据寄存器                                                       */


#define WR_FST_FT_HEALTHWORD(x)    {*(FST_FT_HEALTHWORD) = (x);}


#define WR_SND_FT_HEALTHWORD(x)    {*(SND_FT_HEALTHWORD) = (x);}


#define WR_TRD_FT_HEALTHWORD(x)    {*(TRD_FT_HEALTHWORD) = (x);}


#define WriteAsicReg(addr, value)       (ADDR_READ(addr) = (value))            /* 向ASIC寄存器写数 */


#define zrm 1


/* --- 补充的缺失宏定义（用于通过编译与分析） --- */
#ifndef MASK_LOLO_08
#define MASK_LOLO_08 0xFFu
#endif

#ifndef NUM_WKMD
#define NUM_WKMD 1u
#endif

#ifndef NUM_SCOMPART_GYRGR
#define NUM_SCOMPART_GYRGR 1u
#endif

#ifndef NUM_SCOMPART_STGR
#define NUM_SCOMPART_STGR 1u
#endif

#ifndef NUM_STGR
#define NUM_STGR 1u
#endif

#ifndef NUM_STGRDELAY
#define NUM_STGRDELAY 1u
#endif

#ifndef DSS_XY_NUM
#define DSS_XY_NUM 1u
#endif

#ifndef DSS_Z_NUM
#define DSS_Z_NUM 0u
#endif

#ifndef HAVE_DSSZ
#define HAVE_DSSZ 0u
#endif

#ifndef HAVE_ES
#define HAVE_ES 0u
#endif

#ifndef RAD2DEG
#define RAD2DEG 57.29577951308232f
#endif

#ifndef NUM_COMPART
#define NUM_COMPART 1u
#endif

#ifndef GROUPS_STS_K_CORR
#define GROUPS_STS_K_CORR 1u
#endif

#ifndef SI_KALMAN
#define SI_KALMAN 0u
#endif

#ifndef SI_STS
#define SI_STS 1u
#endif

#ifndef SI_DSS
#define SI_DSS 2u
#endif

#ifndef SI_RIGA
#define SI_RIGA 3u
#endif

#ifndef SI_ES
#define SI_ES 4u
#endif

#ifndef SI_QUATERNION
#define SI_QUATERNION 5u
#endif

#ifndef SI_NO
#define SI_NO 6u
#endif

#ifndef SAM
#define SAM 0u
#endif

#ifndef NULL_STATEMENT
#define NULL_STATEMENT() do { } while (0)
#endif

#ifndef BSP_GIC_ICD_BASEADDR
#define BSP_GIC_ICD_BASEADDR 0x00000000u
#endif

#ifndef BSP_INTR_ICDICTR
#define BSP_INTR_ICDICTR 0x00000000u
#endif

#ifndef BSP_INTR_ICDICPR
#define BSP_INTR_ICDICPR 0x00000000u
#endif

#ifndef ALL_USR_ISR
#define ALL_USR_ISR 0xFFFFFFFFu
#endif

int __var = 0;


#endif // AUTO_GENERATED_COMMON_H
