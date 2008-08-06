/*  FILE: agt_rpc.c

   NETCONF Protocol Operations: RPC Agent Side Support

*********************************************************************
*                                                                   *
*                  C H A N G E   H I S T O R Y                      *
*                                                                   *
*********************************************************************

date         init     comment
----------------------------------------------------------------------
17may05      abb      begun

*********************************************************************
*                                                                   *
*                     I N C L U D E    F I L E S                    *
*                                                                   *
*********************************************************************/
#include  <stdio.h>
#include  <stdlib.h>
#include  <string.h>
#include  <memory.h>

#ifndef _H_procdefs
#include  "procdefs.h"
#endif

#ifndef _H_agt_acm
#include  "agt_acm.h"
#endif

#ifndef _H_agt_cli
#include  "agt_cli.h"
#endif

#ifndef _H_agt_rpc
#include  "agt_rpc.h"
#endif

#ifndef _H_agt_rpcerr
#include  "agt_rpcerr.h"
#endif

#ifndef _H_agt_ses
#include  "agt_ses.h"
#endif

#ifndef _H_agt_util
#include  "agt_util.h"
#endif

#ifndef _H_agt_val
#include  "agt_val.h"
#endif

#ifndef _H_agt_val_parse
#include  "agt_val_parse.h"
#endif

#ifndef _H_agt_xml
#include  "agt_xml.h"
#endif

#ifndef _H_def_reg
#include  "def_reg.h"
#endif

#ifndef _H_dlq
#include  "dlq.h"
#endif

#ifndef _H_log
#include  "log.h"
#endif

#ifndef _H_ncx
#include  "ncx.h"
#endif

#ifndef _H_ncxconst
#include  "ncxconst.h"
#endif

#ifndef _H_obj
#include  "obj.h"
#endif

#ifndef _H_rpc
#include  "rpc.h"
#endif

#ifndef _H_rpc_err
#include  "rpc_err.h"
#endif

#ifndef _H_ses
#include  "ses.h"
#endif

#ifndef _H_status
#include  "status.h"
#endif

#ifndef _H_top
#include  "top.h"
#endif

#ifndef _H_val
#include  "val.h"
#endif

#ifndef _H_val_util
#include  "val_util.h"
#endif

#ifndef _H_xmlns
#include  "xmlns.h"
#endif

#ifndef _H_xml_msg
#include  "xml_msg.h"
#endif

#ifndef _H_xml_util
#include  "xml_util.h"
#endif

#ifndef _H_xml_wr
#include  "xml_wr.h"
#endif

#ifndef _H_yangconst
#include  "yangconst.h"
#endif

/********************************************************************
*                                                                   *
*                       C O N S T A N T S                           *
*                                                                   *
*********************************************************************/

#ifdef DEBUG
#define AGT_RPC_DEBUG 1
#endif


/* hack for <error-path> for a couple corner case errors */
#define RPC_ROOT ((const xmlChar *)"/nc:rpc")


/********************************************************************
*                                                                   *
*                           T Y P E S                               *
*                                                                   *
*********************************************************************/
    

/********************************************************************
*                                                                   *
*                       V A R I A B L E S			    *
*                                                                   *
*********************************************************************/
static boolean agt_rpc_init_done = FALSE;


/********************************************************************
* FUNCTION send_rpc_error_info
*
* Send one <error-info> element on the specified session
* print all the rpc_err_info_t records as child nodes
*
* 
* INPUTS:
*   scb == session control block
*   msg == rpc_msg_t in progress
*   err == error record to use for an error_info Q
*   indent == indent amount
*
* RETURNS:
*   none
*********************************************************************/
static void
    send_rpc_error_info (ses_cb_t *scb,
			 rpc_msg_t  *msg,
			 const rpc_err_rec_t *err,
			 int32  indent)
{
    status_t        res;
    xmlns_id_t      ncid;
    uint32          len;
    rpc_err_info_t *errinfo;
    xmlChar         numbuff[NCX_MAX_NUMLEN];


    /* check if there is any error_info data */
    if (dlq_empty(&err->error_info)) {
	return;
    }

    /* init local vars */
    ncid = xmlns_nc_id();

    /* generate the <error-info> start tag */
    xml_wr_begin_elem_ex(scb, &msg->mhdr, ncid, ncid, NCX_EL_ERROR_INFO, 
	   NULL, FALSE, indent, START);

    if (indent >= 0) {
	indent += NCX_DEF_INDENT;
    }

    /* generate each child variable */
    for (errinfo = (rpc_err_info_t *)dlq_firstEntry(&err->error_info);
	 errinfo != NULL;
	 errinfo = (rpc_err_info_t *)dlq_nextEntry(errinfo)) {

	switch (errinfo->val_btype) {
	case NCX_BT_BINARY:
	case NCX_BT_STRING:
	    if (errinfo->v.strval) {
		if (errinfo->isqname) {
		    xml_wr_qname_elem(scb, &msg->mhdr, 
				      errinfo->val_nsid, errinfo->v.strval, 
				      ncid, errinfo->name_nsid, errinfo->name, 
				      NULL, FALSE, indent);
		} else {
		    xml_wr_string_elem(scb, &msg->mhdr, errinfo->v.strval, 
				       ncid, errinfo->name_nsid, 
				       errinfo->name, 
				       NULL, FALSE, indent);
		}
	    } else {
		SET_ERROR(ERR_INTERNAL_PTR);
	    }
	    break;
	case NCX_BT_INT8:
	case NCX_BT_INT16:
	case NCX_BT_INT32:
	case NCX_BT_INT64:
	case NCX_BT_UINT8:
	case NCX_BT_UINT16:
	case NCX_BT_UINT32:
	case NCX_BT_UINT64:
	case NCX_BT_FLOAT32:
	case NCX_BT_FLOAT64:
	    res = ncx_sprintf_num(numbuff, &errinfo->v.numval, 
			    errinfo->val_btype, &len);
	    if (res == NO_ERR) {
		xml_wr_string_elem(scb, &msg->mhdr, numbuff,
				   ncid, errinfo->name_nsid,
				   errinfo->name, 
				   NULL, FALSE, indent);
	    } else {
		SET_ERROR(res);
	    }
	    break;
	default:
	    if (errinfo->v.cpxval) {
		xml_wr_value_elem(scb, &msg->mhdr, errinfo->v.cpxval,
				  ncid, errinfo->name_nsid, errinfo->name, 
				  NULL, FALSE, indent);
	    } else {
		SET_ERROR(ERR_INTERNAL_PTR);
	    }
	}
    }

    if (indent >= 0) {
	indent -= NCX_DEF_INDENT;
    }

    /* generate the <error-info> end tag */
    xml_wr_end_elem(scb, &msg->mhdr, ncid, NCX_EL_ERROR_INFO, indent);

}  /* send_rpc_error_info */


/********************************************************************
* FUNCTION send_rpc_error
*
* Send one <rpc-error> element on the specified session
* 
* INPUTS:
*   scb == session control block
*   msg == rpc_msg_t in progress
*   err == error record to send
*   indent == starting indent count
*
* RETURNS:
*   status
*********************************************************************/
static status_t
    send_rpc_error (ses_cb_t *scb,
		    rpc_msg_t  *msg,
		    const rpc_err_rec_t *err,
		    int32 indent)
{
    status_t             res, retres;
    xmlns_id_t           ncid;
    rpc_err_info_t      *errinfo;
    xml_attrs_t          attrs;
    xmlChar              buff[12];

    /* init local vars */
    retres = NO_ERR;
    ncid = xmlns_nc_id();

    /* check if any XMLNS decls need to be added to 
     * the <rpc-error> element
     */
    xml_init_attrs(&attrs);
    for (errinfo = (rpc_err_info_t *)dlq_firstEntry(&err->error_info);
	 errinfo != NULL;
	 errinfo = (rpc_err_info_t *)dlq_nextEntry(errinfo)) {
	res = xml_msg_check_xmlns_attr(&msg->mhdr,
				       errinfo->name_nsid,
				       errinfo->badns,
				       &attrs);
	if (res == NO_ERR) {
	    res = xml_msg_check_xmlns_attr(&msg->mhdr, 
					   errinfo->val_nsid,
					   errinfo->badns,
					   &attrs);
	}
	if (res != NO_ERR) {
	    SET_ERROR(res);  /***/
	    retres = res;
	}
    }

    /* generate the <rpc-error> start tag */
    xml_wr_begin_elem_ex(scb, &msg->mhdr, ncid, ncid, NCX_EL_RPC_ERROR, 
			 &attrs, ATTRQ, indent, START);

    xml_clean_attrs(&attrs);

    if (indent >= 0) {
	indent += NCX_DEF_INDENT;
    }

    /* generate the <error-type> field */
    xml_wr_string_elem(scb, &msg->mhdr, ncx_get_layer(err->error_type),
		       ncid, ncid, NCX_EL_ERROR_TYPE, NULL, FALSE, indent);

    /* generate the <error-tag> field */
    xml_wr_string_elem(scb, &msg->mhdr, err->error_tag, ncid, ncid, 
		       NCX_EL_ERROR_TAG, NULL, FALSE, indent);

    /* generate the <error-severity> field */
    xml_wr_string_elem(scb, &msg->mhdr, 
		       rpc_err_get_severity(err->error_severity), ncid,
		       ncid, NCX_EL_ERROR_SEVERITY, NULL, FALSE, indent);

    /* generate the <error-app-tag> field */
    if (err->error_app_tag) {
	xml_wr_string_elem(scb, &msg->mhdr, err->error_app_tag, ncid,
			   ncid, NCX_EL_ERROR_APP_TAG, NULL, FALSE, indent);
    } else if (err->error_res != NO_ERR) {
	/* use the internal error code instead */
	*buff = 0;
	sprintf((char *)buff, "%u", err->error_res);
	if (*buff) {
	    xml_wr_string_elem(scb, &msg->mhdr, buff, ncid, ncid,
			       NCX_EL_ERROR_APP_TAG, NULL, FALSE, indent);
	}
    }

    /* generate the <error-path> field */
    if (err->error_path) {
	xml_wr_string_elem(scb, &msg->mhdr, err->error_path, ncid,
			   ncid, NCX_EL_ERROR_PATH, NULL, FALSE, indent);
    }

    /* generate the <error-message> field */
    if (err->error_message) {
	/* see if there is a xml:lang attribute */
	if (err->error_message_lang) {
	    res = xml_add_attr(&attrs, 0, NCX_EL_LANG, 
		       err->error_message_lang);
	    if (res != NO_ERR) {
		SET_ERROR(res);
		retres = res;
	    }
	}
	xml_wr_string_elem(scb, &msg->mhdr, err->error_message, ncid,
			   ncid, NCX_EL_ERROR_MESSAGE, &attrs,
			   TRUE, indent);
	xml_clean_attrs(&attrs);
    }

    /* print all the <error-info> elements */    
    send_rpc_error_info(scb, msg, err, indent);

    if (indent >= 0) {
	indent -= NCX_DEF_INDENT;
    }

    /* generate the <rpc-error> end tag */
    xml_wr_end_elem(scb, &msg->mhdr, ncid, NCX_EL_RPC_ERROR, indent);

    return retres;

}  /* send_rpc_error */


/********************************************************************
* FUNCTION send_rpc_reply
*
* Operation succeeded or failed
* Return an <rpc-reply>
* 
* INPUTS:
*   scb == session control block
*   msg == rpc_msg_t in progress
*
*********************************************************************/
static void
    send_rpc_reply (ses_cb_t *scb,
		    rpc_msg_t  *msg)
{
    agt_rpc_data_cb_t    agtcb;
    const rpc_err_rec_t *err;
    status_t             res;
    xmlns_id_t           ncid;
    uint64               outbytes;
    boolean              datasend, datawritten;

    res = ses_start_msg(scb);
    if (res != NO_ERR) {
	return;
    }

    /* analyze the <rpc> element and populate the 
     * initial namespace prefix map for this message
     */
    res = xml_msg_build_prefix_map(&msg->mhdr, msg->rpc_in_attrs, 
				   TRUE, !dlq_empty(&msg->mhdr.errQ));
    if (res != NO_ERR) {
	SET_ERROR(res);
	/* try to keep going with the prefix map we have */
    }

    ncid = xmlns_nc_id();

    /* generate the <rpc-reply> start tag */
    xml_wr_begin_elem_ex(scb, &msg->mhdr, 0, ncid, NCX_EL_RPC_REPLY, 
			 msg->rpc_in_attrs, ATTRQ, 0, START);


    /* check if there is data to send 
     * do not use msg->rpc_method as intended, but rather
     * the info in the msg itself; This may need to be
     * changed later, but the standard requires a very
     * specific format to all <rpc-reply> elements
     */
    datasend = (msg->rpc_data || msg->rpc_datacb) ? TRUE : FALSE;

    /* check which reply variant needs to be sent */
    if (dlq_empty(&msg->mhdr.errQ) && !datasend) {
	/* no errors and no data, so send <ok> variant */
	xml_wr_empty_elem(scb, &msg->mhdr, ncid, ncid,
			  NCX_EL_OK, NCX_DEF_INDENT);
    } else {
	/* send rpcResponse variant
	 * 0 or <rpc-error> elements followed by
	 * 0 or 1 <data> element
	 */
	for (err = (const rpc_err_rec_t *)dlq_firstEntry(&msg->mhdr.errQ);
	     err != NULL;
	     err = (const rpc_err_rec_t *)dlq_nextEntry(err)) {
	    res = send_rpc_error(scb, msg, err, NCX_DEF_INDENT);
	    if (res != NO_ERR) {
		SET_ERROR(res);
	    }
	}

	/* check generation of <data> element
	 * If the rpc_data filed is non-NULL, then there is
	 * staticly filled data to send
	 * If the rpc_datacb function pointer is non-NULL,
	 * then this is dynamic reply content, even if the rpc_data
	 * node is not NULL
	 */
	if (datasend) {

	    /* check corner case, just empty data and no data callback */
	    if (!msg->rpc_datacb && !val_has_content(msg->rpc_data)) {
		xml_wr_empty_elem(scb, &msg->mhdr, ncid,
				  ncid, NCX_EL_DATA, NCX_DEF_INDENT);
	    } else {
		xml_wr_begin_elem(scb, &msg->mhdr, ncid, ncid,
				  NCX_EL_DATA, NCX_DEF_INDENT);

		outbytes = SES_OUT_BYTES(scb);

		if (msg->rpc_datacb) {
		    /* use user callback to generate the contents */
		    agtcb = (agt_rpc_data_cb_t)msg->rpc_datacb;
		    res = (*agtcb)(scb, msg, NCX_DEF_INDENT*2);
		    if (res != NO_ERR) {
			SET_ERROR(res);
		    }
		} else {
		    /* just write the contents of the rpc <data> var */
		    xml_wr_val(scb, &msg->mhdr, 
			       msg->rpc_data, NCX_DEF_INDENT*2);
		}

		/* only indent the </data> end tag if any data written */
		datawritten = (outbytes != SES_OUT_BYTES(scb));

		xml_wr_end_elem(scb, &msg->mhdr, ncid, NCX_EL_DATA, 
				(datawritten) ? NCX_DEF_INDENT : -1);
	    }
	} 
    }

    /* generate the <rpc-reply> end tag */
    xml_wr_end_elem(scb, &msg->mhdr, ncid, NCX_EL_RPC_REPLY, 0);

    /* finish the message */
    ses_finish_msg(scb);

}  /* send_rpc_reply */


/********************************************************************
* FUNCTION find_rpc
*
* Find the specified rpc_template_t
*
* INPUTS:
*   modname == module name containing the RPC to find
*   rpcname == RPC method name to find
*
* RETURNS:
*   pointer to retrieved obj_template_t or NULL if not found
*********************************************************************/
static obj_template_t *
    find_rpc (const xmlChar *modname,
	      const xmlChar *rpcname)
{
    obj_template_t  *rpc;
    ncx_node_t       deftyp;

    /* look for the RPC method in the definition registry */
    deftyp = NCX_NT_OBJ;
    rpc = (obj_template_t *)
	def_reg_find_moddef(modname, rpcname, &deftyp);
    return rpc;

}  /* find_rpc */


/********************************************************************
* FUNCTION parse_rpc_input
*
* RPC received, parse parameters against rpcio for 'input'
* 
* INPUTS:
*   scb == session control block
*   msg == rpc_msg_t in progress
    rpc == RPC template to use
*   cbset == RPC callback set to use
*   method == method node
*
* RETURNS:
*   status
*********************************************************************/
static status_t
    parse_rpc_input (ses_cb_t *scb,
	       rpc_msg_t  *msg,
	       obj_rpc_t *rpc,
	       agt_rpc_cbset_t *cbset,
	       xml_node_t  *method)

{
    status_t  res;
    obj_template_t  *obj;
    obj_rpcio_t  *rpcio;
    res = NO_ERR;

    /* check if there is an input parmset specified */
    obj = obj_find_template(&rpc->datadefQ, NULL, YANG_K_INPUT);
    if (obj) {
	rpcio = obj->def.rpcio;

	msg->rpc_agt_state = AGT_RPC_PH_PSD;

	/* check if there is a manual PSD parse callback */
	if (cbset && cbset->acb[AGT_RPC_PH_PSD]) {
	    res = (*cbset->acb[AGT_RPC_PH_PSD])(scb, msg, method);
	} else {
	    res = agt_val_parse_nc(scb, &msg->mhdr, obj, method,
				   NCX_DC_CONFIG, &msg->rpc_input);
	}

#ifdef AGT_RPC_DEBUG
	if (LOGDEBUG3) {
	    log_debug3("\nagt_rpc: parse RPC input state");
	    rpc_err_dump_errors(msg);
	    val_dump_value(&msg->rpc_input, 0);
	}
#endif
    }

    return res;

}  /* parse_rpc_input */


/********************************************************************
* FUNCTION post_psd_state
*
* Fixup parmset after parse phase
* Only call if the RPC has an input PS
*
* INPUTS:
*   scb == session control block
*   msg == rpc_msg_t in progress
*
* RETURNS:
*   status
*********************************************************************/
static status_t
    post_psd_state (ses_cb_t *scb,
		    rpc_msg_t  *msg)
{
    status_t  res;

    /* at this point the input is completely parsed and
     * the syntax is valid.  Now add any missing defaults
     * to the RPC Parmset. 
     */
    res = val_add_defaults(&msg->rpc_input, FALSE);
    if (res == NO_ERR) {
	/* check that the number of instances of the parameters
	 * is reasonable and only one member from any choice is
	 * present (if applicable)
	 *
	 * Make sure to check choice before instance because
	 * any missing choices would be incorrectly interpreted
	 * as multiple missing parameter errors
	 */
	res = agt_val_parse_instance_check(scb, &msg->mhdr, 
					   &msg->rpc_input, 
					   NCX_LAYER_OPERATION);
    }

    return res;

}  /* post_psd_state */


/************** E X T E R N A L   F U N C T I O N S  ***************/

/********************************************************************
* FUNCTION agt_rpc_init
*
* Initialize the agt_rpc module
* Adds the agt_rpc_dispatch function as the handler
* for the NETCONF <rpc> top-level element.
*
* INPUTS:
*   none
* RETURNS:
*   NO_ERR if all okay, the minimum spare requests will be malloced
*********************************************************************/
status_t 
    agt_rpc_init (void)
{
    status_t  res;

    if (!agt_rpc_init_done) {
	res = top_register_node(NC_MODULE, NCX_EL_RPC, agt_rpc_dispatch);
	if (res != NO_ERR) {
	    return res;
	}
	agt_rpc_init_done = TRUE;
    }
    return NO_ERR;

} /* agt_rpc_init */


/********************************************************************
* FUNCTION agt_rpc_cleanup
*
* Cleanup the agt_rpc module.
* Unregister the top-level NETCONF <rpc> element
*
*********************************************************************/
void 
    agt_rpc_cleanup (void)
{
    if (agt_rpc_init_done) {
	top_unregister_node(NC_MODULE, NCX_EL_RPC);
	agt_rpc_init_done = FALSE;
    }

} /* agt_rpc_cleanup */


/********************************************************************
* FUNCTION agt_rpc_register_method
*
* add callback for 1 phase of RPC processing 
*
* INPUTS:
*    module == module name or RPC method
*    method_name == RPC method name
*    phase == RPC agent callback phase for this callback
*    method == pointer to callback function
*
* RETURNS:
*    status of the operation
*********************************************************************/
status_t 
    agt_rpc_register_method (const xmlChar *module,
			     const xmlChar *method_name,
			     agt_rpc_phase_t  phase,
			     agt_rpc_method_t method)
{
    obj_template_t  *rpcobj;
    agt_rpc_cbset_t *cbset;

    if (!module || !method_name || !method) {
	return SET_ERROR(ERR_INTERNAL_PTR);
    }

    /* find the RPC template */
    rpcobj = find_rpc(module, method_name);
    if (!rpcobj) {
	return SET_ERROR(ERR_NCX_DEF_NOT_FOUND);
    }

    /* get the agent CB set, or create a new one */
    if (rpcobj->cbset) {
	cbset = (agt_rpc_cbset_t *)rpcobj->cbset;
    } else {
	cbset = m__getObj(agt_rpc_cbset_t);
	if (!cbset) {
	    return SET_ERROR(ERR_INTERNAL_MEM);
	}
	memset(cbset, 0x0, sizeof(agt_rpc_cbset_t));
	rpcobj->cbset = (void *)cbset;
    }

    /* add the specified method */
    cbset->acb[phase] = method;
    return NO_ERR;

} /* agt_rpc_register_method */


/********************************************************************
* FUNCTION agt_rpc_unsupport_method
*
* mark an RPC method as unsupported within the agent
* this is needed for operations dependent on capabilities
*
* INPUTS:
*    module == module name of RPC method (really module name)
*    method_name == RPC method name
*********************************************************************/
void 
    agt_rpc_unsupport_method (const xmlChar *module,
			      const xmlChar *method_name)
{
    obj_template_t  *rpcobj;

    if (!module || !method_name) {
	SET_ERROR(ERR_INTERNAL_PTR);
	return;
    }

    /* find the RPC template */
    rpcobj = find_rpc(module, method_name);
    if (!rpcobj) {
	SET_ERROR(ERR_NCX_DEF_NOT_FOUND);
	return;
    }

    rpcobj->def.rpc->supported = FALSE;

} /* agt_rpc_unsupport_method */


/********************************************************************
* FUNCTION agt_rpc_unregister_method
*
* remove the callback functions for all phases of RPC processing 
* for the specified RPC method
*
* INPUTS:
*    module == module name of RPC method (really module name)
*    method_name == RPC method name
*********************************************************************/
void 
    agt_rpc_unregister_method (const xmlChar *module,
			       const xmlChar *method_name)
{
    obj_template_t       *rpcobj;

    if (!module || !method_name) {
	SET_ERROR(ERR_INTERNAL_PTR);
	return;
    }

    /* find the RPC template */
    rpcobj = find_rpc(module, method_name);
    if (!rpcobj) {
	SET_ERROR(ERR_NCX_DEF_NOT_FOUND);
	return;
    }

    /* get the agent CB set and delete it */
    if (rpcobj->cbset) {
	m__free(rpcobj->cbset);
	rpcobj->cbset = NULL;
    }

} /* agt_rpc_unregister_method */


/********************************************************************
* FUNCTION agt_rpc_dispatch
*
* Dispatch an incoming <rpc> request
*
* INPUTS:
*   scb == session control block
*   top == top element descriptor
*********************************************************************/
void 
    agt_rpc_dispatch (ses_cb_t *scb,
		      xml_node_t *top)
{
    rpc_msg_t       *msg;
    xml_attr_t      *attr;
    obj_template_t  *rpcobj;
    obj_rpc_t       *rpc;
    agt_rpc_cbset_t *cbset;
    xmlChar         *buff;
    xml_node_t       method, testnode;
    status_t         res;
    xml_attr_t       errattr;
    boolean          errdone;

#ifdef DEBUG
    if (!scb || !top) {
	SET_ERROR(ERR_INTERNAL_PTR);
	return;
    }
#endif

    /* init local vars */
    res = NO_ERR;
    cbset = NULL;

    /* make sure any real session has been properly established */
    if (scb->type != SES_TYP_DUMMY && scb->state != SES_ST_IDLE) {
	res = ERR_NCX_ACCESS_DENIED;
	/* TBD: stats update */
	log_info("\nagt_rpc dropping session %d (%d) %s",
		  scb->sid, res, get_error_string(res));
	agt_ses_request_close(scb->sid);
	return;
    }

    /* make sure 'rpc' is the right kind of node */
    if (top->nodetyp != XML_NT_START) {
	res = ERR_NCX_WRONG_NODETYP;
	scb->stats.in_err_msgs++;
	return;
    }

    /* the current node is 'rpc' in the netconf namespace
     * First get a new RPC message struct
     */
    msg = rpc_new_msg();
    if (!msg) {
	res = ERR_INTERNAL_MEM;
	scb->stats.in_err_msgs++;
	/* TBD: send_opfailed_reply */
	return;
    }

    /* setup the struct as an incoming RPC message */
    msg->rpc_incoming = TRUE;
    msg->rpc_module = top->module;
    msg->rpc_nsid = top->nsid;

    /* borrow the top->attrs queue without copying it 
     * The rpc-reply phase may add attributes to this list
     * that the caller will free ater this function returns
     */
    msg->rpc_in_attrs = &top->attrs;

    /* get the NCX RPC group-id attribute if present 
     * don't really care about the error -- keep going
     */
    attr = xml_find_attr(top, xmlns_ncx_id(), NCX_EL_GROUP_ID);
    if (attr && attr->attr_val) {
	res = ncx_decode_num(attr->attr_val, NCX_BT_UINT32, &msg->rpc_group);
	if (res != NO_ERR) {
	    agt_record_attr_error(scb, &msg->mhdr.errQ, NCX_LAYER_RPC,
		  res, attr, top, NULL, NCX_NT_STRING, RPC_ROOT);
	    res = NO_ERR;
	}
    }

    /* get the NCX RPC with-defaults attribute if present */
    attr = xml_find_attr(top, xmlns_ncx_id(), NCX_EL_WITH_DEFAULTS);
    if (attr && attr->attr_val) {
	if (ncx_is_true(attr->attr_val)) {
	    msg->mhdr.withdef = TRUE;
	} else if (ncx_is_false(attr->attr_val)) {
	    msg->mhdr.withdef = FALSE;
	} else {
	    /* else this is an invalid-attribute error !!! */
	    agt_record_attr_error(scb, &msg->mhdr.errQ, NCX_LAYER_RPC,
				  ERR_NCX_BAD_ATTRIBUTE, attr, top, NULL, 
				  NCX_NT_STRING, RPC_ROOT);
	}
    } else {
	/* with-defaults not explicitly set, so get the default */
	msg->mhdr.withdef = ses_withdef(scb);	
    }

    /* get the NCX RPC with-metadata attribute if present */
    attr = xml_find_attr(top, xmlns_ncx_id(), NCX_EL_WITH_METADATA);
    if (attr && attr->attr_val) {
	if (ncx_is_true(attr->attr_val)) {
	    msg->mhdr.withmeta = TRUE;
	} else if (ncx_is_false(attr->attr_val)) {
	    msg->mhdr.withmeta = FALSE;
	} else {
	    /* else this is an invalid-attribute error !!! */
	    agt_record_attr_error(scb, &msg->mhdr.errQ, NCX_LAYER_RPC,
				  ERR_NCX_BAD_ATTRIBUTE, attr, top, NULL, 
				  NCX_NT_STRING, RPC_ROOT);
	}
    } else {
	/* with-metadata not explicitly set, so get the default */
	msg->mhdr.withmeta = ses_withmeta(scb);	
    }

    /* get the NC RPC message-id attribute; must be present */
    attr = xml_find_attr(top, xmlns_nc_id(), NCX_EL_MESSAGE_ID);
    if (attr && attr->attr_val) {
	msg->rpc_msg_id = attr->attr_val;
    } else {
	res = ERR_NCX_MISSING_ATTRIBUTE;
	    
	memset(&errattr, 0x0, sizeof(xml_attr_t));
	errattr.attr_ns = xmlns_nc_id();
	errattr.attr_name = NCX_EL_MESSAGE_ID;
	errattr.attr_val = (xmlChar *)NULL;

	agt_record_attr_error(scb, &msg->mhdr.errQ, NCX_LAYER_RPC,
			      res, &errattr, top, NULL, NCX_NT_STRING,
			      RPC_ROOT);
    }

    /* check any errors in the <rpc> node */
    if (res != NO_ERR) {
	msg->rpc_status = res;
	send_rpc_reply(scb, msg);
	rpc_free_msg(msg);
	return;
    }

    /* get the next XML node, which is the RPC method name */
    xml_init_node(&method);
    res = agt_xml_consume_node(scb->reader, &method,
	   NCX_LAYER_RPC, &msg->mhdr.errQ);
    if (res != NO_ERR) {
	errdone = TRUE;
    } else {
	errdone = FALSE;

#ifdef AGT_RPC_DEBUG
	log_debug("\nagt_rpc: got method node (%s)", method.elname);
	if (LOGDEBUG2) {
	    xml_dump_node(&method);
	}
#endif

	/* check the node type which should be type start or simple */
	if (!(method.nodetyp==XML_NT_START || 
	      method.nodetyp==XML_NT_EMPTY)) {
	    res = ERR_NCX_WRONG_NODETYP;
	} else {
	    /* look for the RPC method in the definition registry */
	    rpcobj = find_rpc(method.module, method.elname);
	    rpc = (rpcobj) ? rpcobj->def.rpc : NULL;
	    if (!rpc) {
		res = ERR_NCX_DEF_NOT_FOUND;
	    } else if (!rpc->supported) {
		res = ERR_NCX_OPERATION_NOT_SUPPORTED;
	    } else if (!agt_acm_rpc_allowed(scb->username, rpcobj)) {
		res = ERR_NCX_ACCESS_DENIED;
	    } else {
		/* get the agent callback set for this RPC 
		 * if NULL, no agent instrumentation has been 
		 * registered yet for this RPC method
		 */
		cbset = (agt_rpc_cbset_t *)rpcobj->cbset;

		/* finish setting up the rpc_msg_t struct */
		msg->rpc_meth_nsid = method.nsid;
		msg->rpc_meth_name = method.elname;
		msg->rpc_method = rpc;
	    }
	}
    }

    /* check any errors in the RPC method node */
    if (res != NO_ERR && !errdone) {
	/* construct an error-path string */
	buff = m__getMem(xml_strlen(method.elname) + 6);
	if (buff) {
	    xml_strcpy(buff, RPC_ROOT);
	    xml_strcat(buff, (const xmlChar *)"/");
	    xml_strcat(buff, method.elname);
	}
	/* passing a NULL buff is okay; it will get checked 
 	 * The NCX_NT_STRING node type enum is ignored if 
	 * the buff pointer is NULL
	 */
	agt_record_error(scb, &msg->mhdr.errQ, NCX_LAYER_RPC, res, 
		 &method, NCX_NT_NONE, NULL, NCX_NT_STRING, buff);
	if (buff) {
	    m__free(buff);
	}
    }

    /* change the session state */
    scb->state = SES_ST_IN_MSG;

    /* RPC setup state */
    if (res == NO_ERR && cbset && cbset->acb[AGT_RPC_PH_SETUP]) {
	msg->rpc_agt_state = AGT_RPC_PH_SETUP;
	res = (*cbset->acb[AGT_RPC_PH_SETUP])(scb, msg, &method);
    }

    /* parameter set parse state */
    if (res == NO_ERR) {
	res = parse_rpc_input(scb, msg, rpc, cbset, &method);
    }

    /* read in a node which should be the endnode to match 'top' */
    xml_init_node(&testnode);
    if (res == NO_ERR) {
	res = agt_xml_consume_node(scb->reader, &testnode,
				   NCX_LAYER_RPC, &msg->mhdr.errQ);
    }
    if (res == NO_ERR) {
#ifdef AGT_RPC_DEBUG
	log_debug2("\nagt_rpc: expecting %s end node", top->qname);
	if (LOGDEBUG3) {
	    xml_dump_node(&testnode);
	}
#endif
	res = xml_endnode_match(top, &testnode);
    }
    xml_clean_node(&testnode);


    /* check that there is nothing after the <rpc> element */
    if (res == NO_ERR && !xml_docdone(scb->reader)) {
	msg->rpc_status = ERR_NCX_UNKNOWN_ELEMENT;

	/* get all the extra nodes and report the errors */
	res = NO_ERR;
	while (res==NO_ERR) {
	    /* do not add errors such as unknown namespace */
	    res = agt_xml_consume_node(scb->reader, &testnode,
		   NCX_LAYER_NONE, NULL);
	    if (res==NO_ERR) {
		res = ERR_NCX_UNKNOWN_ELEMENT;
		agt_record_error(scb, &msg->mhdr.errQ, NCX_LAYER_RPC, res, 
			 &method, NCX_NT_NONE, NULL, NCX_NT_STRING, RPC_ROOT);
	    }
	}

	/* reset the error status */
	res = ERR_NCX_UNKNOWN_ELEMENT;
    } 
    xml_clean_node(&testnode);

    /* check the defaults and any choices if there is an input PS */
    if (res == NO_ERR && obj_find_child(rpcobj, NULL, YANG_K_INPUT)) {
	res = post_psd_state(scb, msg);
    }

    /* validate state */
    if ((res==NO_ERR) && (cbset && cbset->acb[AGT_RPC_PH_VALIDATE])) {
	/* input passes the basic NCX schema tests at this point;
	 * check if there is a validate callback for
	 * referential integrity, locks, resource reservation, etc.
	 * Only the top level parmset has been checked for instance
	 * qualifer usage.  The caller must do Data Parmset instance
	 * validataion in this VALIDATE callback, as needed
	 */
	msg->rpc_agt_state = AGT_RPC_PH_VALIDATE;
	res = (*cbset->acb[AGT_RPC_PH_VALIDATE])(scb, msg, &method);
    }

    /* there does not always have to be an invoke callback */
    if ((res==NO_ERR) && cbset && cbset->acb[AGT_RPC_PH_INVOKE]) {
	msg->rpc_agt_state = AGT_RPC_PH_INVOKE;
	res = (*cbset->acb[AGT_RPC_PH_INVOKE])(scb, msg, &method);
    }

    /* check if there is a pre-reply callback */
    if ((res == NO_ERR) && cbset && cbset->acb[AGT_RPC_PH_PRERPY]) {
	msg->rpc_agt_state = AGT_RPC_PH_PRERPY;
	res = (*cbset->acb[AGT_RPC_PH_PRERPY])(scb, msg, &method);
    }

    /* reply state 
     * check if there is a manual override reply callback 
     */
    if (res != NO_ERR) {
	msg->rpc_status = res;
    }
    msg->rpc_agt_state = AGT_RPC_PH_RPY;
    if (cbset && cbset->acb[AGT_RPC_PH_RPY]) {
	/* ignore the callback response to avoid sending double errors */
	(void)(*cbset->acb[AGT_RPC_PH_RPY])(scb, msg, &method);
    } else {
	send_rpc_reply(scb, msg);
    }

    /* only reset the session state to idle if was not changed
     * to SES_ST_SHUTDOWN_REQ during this RPC call
     */
    if (scb->state == SES_ST_IN_MSG) {
	scb->state = SES_ST_IDLE;
    }

    /* cleanup and exit */
    xml_clean_node(&method);
    rpc_free_msg(msg);

#ifdef AGT_RPC_DEBUG
    print_errors();
    clear_errors();
#endif

} /* agt_rpc_dispatch */


/********************************************************************
* FUNCTION agt_rpc_load_config_file
*
* Dispatch an internal <load-config> request
*
*    - Create a dummy session and RPC message
*    - Call a special agt_ps_parse function to parse the config file
*    - Call the special agt_ncx function to invoke the proper 
*      parmset and application 'validate' callback functions, and 
*      record all the error/warning messages
*    - Call the special ncx_agt function to invoke all the 'apply'
*      callbacks as needed
*    - transfer any error messages to the cfg->load_errQ
*
* INPUTS:
*   filespec == XML config filespec to load
*   cfg == cfg_template_t to fill in
*
* RETURNS:
*     status
*********************************************************************/
status_t
    agt_rpc_load_config_file (const xmlChar *filespec,
			      cfg_template_t  *cfg)
{
    ses_cb_t        *scb;
    rpc_msg_t       *msg;
    obj_template_t  *rpcobj;
    obj_rpc_t       *rpc;
    agt_rpc_cbset_t *cbset;
    xml_node_t       method;
    status_t         res;
    boolean          valdone;

#ifdef DEBUG
    if (!filespec || !cfg) {
	return SET_ERROR(ERR_INTERNAL_PTR);
    }
#endif

    /* first make sure the load-config RPC is registered */
    rpcobj = find_rpc(AGT_CLI_MODULE, NCX_EL_LOAD_CONFIG);
    if (!rpcobj) {
	return SET_ERROR(ERR_INTERNAL_VAL);
    }

    /* make sure the agent callback set for this RPC is ok */
    cbset = (agt_rpc_cbset_t *)rpcobj->cbset;
    if (!cbset) {
	return SET_ERROR(ERR_INTERNAL_VAL);
    }
    rpc = rpcobj->def.rpc;

    /* make sure the config is in the init state */
    if (cfg->cfg_state != CFG_ST_INIT) {
	return SET_ERROR(ERR_INTERNAL_VAL);
    }

    /* create a dummy session control block */
    scb = agt_ses_new_dummy_session();
    if (!scb) {
	return ERR_INTERNAL_MEM;
    }

    /* create a dummy RPC msg */
    msg = rpc_new_msg();
    if (!msg) {
	agt_ses_free_dummy_session(scb);
	return ERR_INTERNAL_MEM;
    }

    /* setup the config file as the xmlTextReader input */
    res = xml_get_reader_from_filespec((const char *)filespec, 
				       &scb->reader);
    if (res != NO_ERR) {
	rpc_free_msg(msg);
	agt_ses_free_dummy_session(scb);
	return res;
    }

    msg->rpc_incoming = TRUE;
    msg->rpc_nsid = 0;    /* no default NS !! */
    msg->rpc_module = NC_MODULE;
    msg->rpc_in_attrs = NULL;
    msg->rpc_group.u = 0;
    msg->rpc_msg_id = (const xmlChar *)"1";

    /* create a dummy method XML node */
    xml_init_node(&method);
    method.nodetyp = XML_NT_START;
    method.nsid = 0;
    method.module = AGT_CLI_MODULE;
    method.qname = NCX_EL_LOAD_CONFIG;
    method.elname = NCX_EL_LOAD_CONFIG;
    method.depth = 1;

    msg->rpc_meth_nsid = method.nsid;
    msg->rpc_meth_name = method.elname;
    msg->rpc_method = rpc;
    msg->rpc_user1 = cfg;
    msg->rpc_err_option = OP_ERROP_CONTINUE;

    res = NO_ERR;
    valdone = FALSE;

    /* parse the config file as a parameter set */
    if (res == NO_ERR) {
	res = parse_rpc_input(scb, msg, rpc, cbset, &method);
	if (res == NO_ERR) {
	    res = post_psd_state(scb, msg);
	}
    }

    /* call all the parmset validate callbacks */
    if (res==NO_ERR && cbset->acb[AGT_RPC_PH_VALIDATE]) {
	msg->rpc_agt_state = AGT_RPC_PH_VALIDATE;
	res = (*cbset->acb[AGT_RPC_PH_VALIDATE])(scb, msg, &method);
	valdone = TRUE;
    }

    /* call all the parmset invoke callbacks */
    if (valdone && cbset->acb[AGT_RPC_PH_INVOKE]) {
	msg->rpc_agt_state = AGT_RPC_PH_INVOKE;
	res = (*cbset->acb[AGT_RPC_PH_INVOKE])(scb, msg, &method);
    }

#ifdef DEBUG
    if (!dlq_empty(&msg->mhdr.errQ)) {
	rpc_err_dump_errors(msg);
    }
#endif

    /* move any error messages to the config error Q */
    dlq_block_enque(&msg->mhdr.errQ, &cfg->load_errQ);

    /* cleanup and exit */
    xml_clean_node(&method);
    rpc_free_msg(msg);
    agt_ses_free_dummy_session(scb);

    return res;

} /* agt_rpc_load_config_file */


/* END file agt_rpc.c */
