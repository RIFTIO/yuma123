#ifndef _H_b64
#define _H_b64

/*  FILE: b64.h
*********************************************************************
*								    *
*			 P U R P O S E				    *
*								    *
*********************************************************************

    RFC 4648 base64 support, from b64.c

*********************************************************************
*								    *
*		   C H A N G E	 H I S T O R Y			    *
*								    *
*********************************************************************

date	     init     comment
----------------------------------------------------------------------
25-oct-08    abb      Begun

*/

#ifndef _H_status
#include "status.h"
#endif

/********************************************************************
*								    *
*			F U N C T I O N S			    *
*								    *
*********************************************************************/

extern status_t
    b64_encode (const unsigned char *inbuff,
		unsigned int inbufflen,
		unsigned char *outbuff, 
		unsigned int outbufflen,
		unsigned int linesize,
		unsigned int *retlen);


extern status_t
    b64_decode (const unsigned char *inbuff, 
		unsigned int inbufflen,
		unsigned char *outbuff,
		unsigned int outbufflen,
		unsigned int *retlen);

#endif	    /* _H_b64 */