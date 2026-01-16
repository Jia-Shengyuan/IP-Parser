void B_TcProcess(unint08* tcaData)
{
	unint08 chksum;
	unint08 i;

	if ((tcaData[0] == 0xE1) && (tcaData[1] == 0x00))					/* 包头正确 */
	{		
		CheckCal(3, &tcaData[0], &chksum);
	    if(tcaData[3] == chksum)
	    {
	    	/* 校验和正确 */
	    	if(tcaData[2] == 0)
	    	{
	    		TR32_FLGMODE_VALUE(SAM_DAMP) ;							/* 速率阻尼方式 */
	    	}
	    	else if(tcaData[2] == 1)
	    	{
	    		TR32_FLGMODE_VALUE(SAM_CRUISE) ;					    /* 进巡航模式 */
	    	}
	    	else
	    	{
	    		TR32_FLGMODE_VALUE(NOCTRL) ;					    	/* 进不控模式 */
	    	}
	    }
	}

	return;
}