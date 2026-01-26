#include "IP_B_TcProcess.h"

// =======================================================
// 函数实现
// =======================================================

void CheckCal(const unint32 len, const unint08 *pkv, unint08 *chksum)
{
	unint32 i;
	chksum = 0;

	for(i=0; i<len; i++)
	{
	    chksum = chksum + pkv[i];
	}

	return;
}

void B_TcProcess(unint08* tcaData)
{
	unint08 chksum;
	unint08 i;

	if ((tcaData[0] == 0xE1) && (tcaData[1] == 0x00))					
	{		
		CheckCal(3, &tcaData[0], &chksum);
	    if(tcaData[3] == chksum)
	    {
	    	if(tcaData[2] == 0)
	    	{
	    		TR32_FLGMODE_VALUE(SAM_DAMP) ;							
	    	}
	    	else if(tcaData[2] == 1)
	    	{
	    		TR32_FLGMODE_VALUE(SAM_CRUISE) ;					    
	    	}
	    	else
	    	{
	    		TR32_FLGMODE_VALUE(NOCTRL) ;					    	
	    	}
	    }
	}

	return;
}