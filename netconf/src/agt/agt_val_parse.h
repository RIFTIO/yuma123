#ifndef _H_agt_val_parse
#define _H_agt_val_parse

/*  FILE: agt_val_parse.h
*********************************************************************
*								    *
*			 P U R P O S E				    *
*								    *
*********************************************************************

    Parameter Value Parser Module

*********************************************************************
*								    *
*		   C H A N G E	 H I S T O R Y			    *
*								    *
*********************************************************************

date	     init     comment
----------------------------------------------------------------------
11-feb-06    abb      Begun

*/

#ifndef _H_rpc
#include "rpc.h"
#endif

#ifndef _H_ses
#include "ses.h"
#endif

#ifndef _H_status
#include "status.h"
#endif

#ifndef _H_typ
#include "typ.h"
#endif

#ifndef _H_xml_util
#include "xml_util.h"
#endif

/********************************************************************
*								    *
*			F U N C T I O N S			    *
*								    *
*********************************************************************/

/* parse a value for an object from a NETCONF PDU XML stream */
extern status_t 
    agt_val_parse_nc (ses_cb_t  *scb,
		      xml_msg_hdr_t *msg,
		      const obj_template_t *obj,
		      const xml_node_t *startnode,
		      ncx_data_class_t parentdc,
		      val_value_t *parmval);

status_t 
    agt_val_parse_instance_check (ses_cb_t *scb,
				  xml_msg_hdr_t *msg,
				  val_value_t *valset,
				  ncx_layer_t   layer);

#endif	    /* _H_agt_val_parse */
