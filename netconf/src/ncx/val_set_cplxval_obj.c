#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <memory.h>
#include <string.h>
#include <ctype.h>
#include <xmlstring.h>

#include "procdefs.h"
#include "b64.h"
#include "cfg.h"
#include "dlq.h"
#include "getcb.h"
#include "json_wr.h"
#include "log.h"
#include "ncx.h"
#include "ncx_list.h"
#include "ncx_num.h"
#include "ncx_str.h"
#include "ncxconst.h"
#include "obj.h"
#include "ses.h"
#include "tk.h"
#include "typ.h"
#include "val.h"
#include "val_util.h"
#include "xml_util.h"
#include "xml_wr.h"
#include "xpath.h"
#include "xpath1.h"
#include "xpath_yang.h"
#include "yangconst.h"

static status_t val_set_cplxval_obj_recursive_anyxml(val_value_t *val, obj_template_t *obj, xmlDocPtr doc, xmlNode *top)
{
    xmlNode *cur;
    status_t res;

    cur = top->xmlChildrenNode;
    while (cur != NULL) {
        if(cur->children->type == XML_ELEMENT_NODE) {
            /* container */
            val_value_t* container_val;
            container_val = val_new_child_val(obj_get_nsid(val->obj), obj_get_name(val->obj), TRUE, val, 0/*get_editop(&nextnode)*/, ncx_get_gen_container());
            res = val_set_cplxval_obj_recursive_anyxml(container_val, obj, doc, cur);
            if(res != NO_ERR) {
                return res;
            }
        } else {
            /* leaf */ 
            val_value_t* leaf_val;
            char* value_str;
            value_str = xmlNodeListGetString(doc, cur->xmlChildrenNode, 1);
            assert(value_str!=NULL);
            leaf_val = val_new_value();
            assert(leaf_val!=NULL);
            val_set_string (leaf_val,
                            cur->name,
                            value_str);
            xmlFree(value_str);
            val_add_child(leaf_val, val);
        }
        cur = cur->next;
    }

    return NO_ERR;
}

status_t val_set_cplxval_obj_recursive(val_value_t *val, obj_template_t *obj, xmlDocPtr doc, xmlNode *top)
{
    xmlNode *cur;
    status_t res;

    for(cur=top->xmlChildrenNode; cur!=NULL; cur=cur->next) {
        obj_template_t *cur_obj;
        val_value_t* cur_val;

        cur_obj = obj_find_child(val->obj,
                                 obj_get_mod_name(val->obj),
                                 cur->name);
        if(cur_obj==NULL) {
            continue;
        }
        cur_val = val_new_value();
        assert(cur_val!=NULL);

        val_init_from_template(cur_val, cur_obj);
        if(typ_is_simple(obj_get_basetype(cur_obj))) {
            char* value_str;
            value_str = xmlNodeListGetString(doc, cur->xmlChildrenNode, 1);
            assert(value_str != NULL);
            res = val_set_simval_obj(
                    cur_val,
                    cur_val->obj,
                    value_str
                    );
            assert(res==NO_ERR);
            xmlFree(value_str);

        } else if(cur_obj->objtype == OBJ_TYP_ANYXML) {
            res = val_set_cplxval_obj_recursive_anyxml(cur_val, cur_obj, doc, cur);
            assert(res==NO_ERR);
        } else {
            res = val_set_cplxval_obj_recursive(cur_val, cur_obj, doc, cur);
            assert(res==NO_ERR);
        }
        val_add_child(cur_val, val);
    }
    return NO_ERR;
}

status_t val_set_cplxval_obj(val_value_t *val, obj_template_t *obj, char* xmlstr)
{
    status_t res;
    xmlDocPtr doc;
    xmlNode *top_node;

    doc = xmlReadMemory(xmlstr, strlen(xmlstr), "xmlstr", NULL, 0);
    assert(doc != NULL);

    top_node = xmlDocGetRootElement(doc);

    assert(0==xmlStrcmp(top_node->name, (const xmlChar *)val->name));
    res = val_set_cplxval_obj_recursive(val, obj, doc, top_node);
    assert(res==NO_ERR);
    xmlFreeDoc(doc);
    return NO_ERR;
}
