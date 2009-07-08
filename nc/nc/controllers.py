import turbogears as tg
from turbogears import controllers, expose, flash, widgets, validators, \
    error_handler, validate, redirect, identity
from turbogears.widgets import CSSLink, JSLink, Widget, JumpMenu;
import pkg_resources
import cherrypy
import os
import logging

from cherrypy import request, response
from nc import model
from model import *
from nc import json

import yang_utils
from yang_utils import *

from tg_expanding_form_widget.tg_expanding_form_widget import ExpandingForm

from tw.extjs import TreeView

from nc.registration import controllers as reg_controllers

from nc.NcquickmodController import controllers as NcquickmodController

extTree = TreeView(divID='treeView1', fetch='fetchTree')

log = logging.getLogger("nc.controllers")


#############################################################################
#
# show module jump menu
#
def createModuleJumpMenu():
    """Return the module report jump menu called ncquickmods in the SQL db
    """

    ncquickmods = Ncquickmod.select(orderBy=Ncquickmod.q.modname)
    options = [('/', "Show Module Report")]
    for ncquickmod in ncquickmods:
        options.append(("/modulereport/" + ncquickmod.modname, ncquickmod.modname))

    modmenu = JumpMenu(field_class="ncheader_menu", options=options)
    return modmenu


#############################################################################
# use a static variable to hold the module menu
# instead of generating it every time.
# when the module update code is added, it will need 
# to replace this var when modules are added or deleted
# from the database
moduleJumpMenu = createModuleJumpMenu()


#############################################################################
#
# for breadcrumbs -- this does not work yet not used!!!
#
def createNavBarLinks():
    """Return link information for constructing bread crumb navigation.
    """
    cherry_trail = cherrypy._cputil.get_object_trail()
    href = tg.url('/')
    crumbs = [(href, 'home')]
    for item in cherry_trail:
        # item[0] is the name you use in the URL to access the controller.
        # item[1] is the actual controller
        #if isinstance(item[1], (Controller, BaseDataController)):
        if item[1] is not None:
            if item[0] != 'root' and item[0] != 'index' \
                    and item[0] != 'default':
                href = "%s%s/" % (href, item[0])
                crumbs.append([href, item[0]])
    return crumbs


#############################################################################
#
# Run yangdump Validation Schemas
#
class RunYangFormSchema(validators.Schema):
    depfile = validators.FieldStorageUploadConverter(not_empty=False)

class RunYangExpandingFormSchema(validators.Schema):
    depfiles = validators.ForEach(RunYangFormSchema(),)

##############################################################################
#
# Run yangdump Form Widgets
#
# srcfile is the 1 mandatory parameter
srcfile = widgets.FileField(validator=validators.FieldStorageUploadConverter(not_empty=True),
                            name='srcfile',
                            label=_(u'Select YANG source module\n'))

modversion = widgets.CheckBox(name='modversion', default=False,
                              label='Include module version report')
exports = widgets.CheckBox(name='exports', default=False,
                              label='Include exported symbols report')
dependencies = widgets.CheckBox(name='dependencies', default=False,
                              label='Include external dependencies report')
identifiers = widgets.CheckBox(name='identifiers', default=False,
                              label='Include object identifiers report')

# 0 or more dependency files can also be entered
depfile = widgets.FileField(name='depfile', label='')

# this creates the expanding part of the form
expform = ExpandingForm(
    name='depfiles',
    label=_(u'Add optional import or include file(s)'),
    fields=[depfile],)

# this creates the entire run yangdump form
runyangdump_form = widgets.ListForm(
    'runyangdumpform',
    fields = [srcfile, expform, modversion, exports, dependencies, identifiers],
    action = 'runyangdump',
    submit_text = _(u'Submit Files'),
    validator = RunYangExpandingFormSchema()
)


##############################################################################
#
# Run yangdiff Validation Schemas
#
class RunDiffFormSchema(validators.Schema):
    depfile = validators.FieldStorageUploadConverter(not_empty=False)

class RunDiffExpandingFormSchema(validators.Schema):
    depfiles = validators.ForEach(RunDiffFormSchema(),)

##############################################################################
#
# Run yangdump Form Widgets
#
# srcfile is the 1 mandatory parameter
oldfile = widgets.FileField(validator=validators.FieldStorageUploadConverter(not_empty=True),
                            name='oldfile',
                            label=_(u'Select older YANG source module\n'))

newfile = widgets.FileField(validator=validators.FieldStorageUploadConverter(not_empty=True),
                            name='newfile',
                            label=_(u'Select newer YANG source module\n'))


# this creates the entire run yangdump form
runyangdiff_form = widgets.ListForm(
    'runyangdiffform',
    fields = [oldfile, newfile, expform],
    action = 'runyangdiff',
    submit_text = _(u'Submit Files'),
    validator = RunDiffExpandingFormSchema()
)


##############################################################################
#
# form fields for the search database form
#
class ModuleSearchFields(widgets.WidgetsList):
    """Setup the form fields for the module portion of the search database page
    """
    matchtype = widgets.RadioButtonList(name='matchtype',
                                           label="Module Match type:",
                                           validator=validators.NotEmpty,
                                           default='All',
                                           options=['All','Any'])
    modnamepart = widgets.TextField(name='modnamepart',
                                    label="Enter all or part of the module name",
                                    validator = validators.UnicodeString(if_empty = None),
                                    attrs=dict(size="40"))
    modprefix = widgets.TextField(name='modprefix',
                                  label="Enter the entire module prefix",
                                  validator = validators.UnicodeString(if_empty = None),
                                  attrs=dict(size="40"))
    moddate = widgets.CalendarDatePicker(name='moddate',
                                         label='Enter a revision date (yyyy-mm-dd)',
                                         calendar_lang='en',
                                         format='%Y-%m-%d',
                                         default='',
                                         button_text='Changed since this date',
                                         validator=validators.DateTimeConverter(format="%Y-%m-%d"))


##############################################################################
#
# form fields for the search database form
#
class TypedefSearchFields(widgets.WidgetsList):
    """Setup the form fields for the typedef portion of the search database page
    """
    matchtype = widgets.RadioButtonList(name='matchtype',
                                        label="Typedef Match type:",
                                        validator=validators.NotEmpty,
                                        default='All',
                                        options=['All','Any'])
    modnamepart = widgets.TextField(name='modnamepart',
                                    label="Enter all or part of the module name",
                                    validator = validators.UnicodeString(if_empty = None),
                                    attrs=dict(size="40"))
    typnamepart = widgets.TextField(name='typnamepart',
                                    label="Enter all or part of the type name",
                                    validator = validators.UnicodeString(if_empty = None),
                                    attrs=dict(size="40"))
    moddate = widgets.CalendarDatePicker(name='moddate',
                                         label='Enter a revision date (yyyy-mm-dd)',
                                         calendar_lang='en',
                                         format='%Y-%m-%d',
                                         default='',
                                         button_text='Changed since this date',
                                         validator=validators.DateTimeConverter(format="%Y-%m-%d"))


##############################################################################
#
# form fields for the search database form
#
class ObjectSearchFields(widgets.WidgetsList):
    """Setup the form fields for the object portion of the search database page
    """
    matchtype = widgets.RadioButtonList(name='matchtype',
                                        label="Object Match type:",
                                        validator=validators.NotEmpty,
                                        default='All',
                                        options=['All','Any'])
    modnamepart = widgets.TextField(name='modnamepart',
                                    label="Enter all or part of the module name",
                                    validator = validators.UnicodeString(if_empty = None),
                                    attrs=dict(size="40"))
    objnamepart = widgets.TextField(name='objnamepart',
                                    label="Enter all or part of the object name",
                                    validator = validators.UnicodeString(if_empty = None),
                                    attrs=dict(size="40"))
    moddate = widgets.CalendarDatePicker(name='moddate',
                                         label='Enter a revision date (yyyy-mm-dd)',
                                         calendar_lang='en',
                                         format='%Y-%m-%d',
                                         default='',
                                         button_text='Changed since this date',
                                         validator=validators.DateTimeConverter(format="%Y-%m-%d"))


#################################################################################
#
# form fields for the search database form
#
class TypeUsageSearchFields(widgets.WidgetsList):
    """Setup the form fields for the type name usage portion of the search database page
    """
    matchtype = widgets.RadioButtonList(name='matchtype',
                                           label="Type Name Match type:",
                                           validator=validators.NotEmpty,
                                           default='Contains',
                                           options=['Contains', 'Exact','Starts with', 'Ends with'])
    typnamepart = widgets.TextField(name='typnamepart',
                                    label="Enter all or part of the type name",
                                    validator = validators.UnicodeString(not_empty=True),
                                    attrs=dict(size="40"))



#################################################################################
#
# form fields for the search database form
#
class ExtensionSearchFields(widgets.WidgetsList):
    """Setup the form fields for the extension portion of the search database page
    """
    matchtype = widgets.RadioButtonList(name='matchtype',
                                        label="Extension Match type:",
                                        validator=validators.NotEmpty,
                                        default='All',
                                        options=['All','Any'])
    modnamepart = widgets.TextField(name='modnamepart',
                                    label="Enter all or part of the module name",
                                    validator = validators.UnicodeString(if_empty = None),
                                    attrs=dict(size="40"))
    extnamepart = widgets.TextField(name='extnamepart',
                                    label="Enter all or part of the extension name",
                                    validator = validators.UnicodeString(if_empty = None),
                                    attrs=dict(size="40"))
    moddate = widgets.CalendarDatePicker(name='moddate',
                                         label='Enter a revision date (yyyy-mm-dd)',
                                         calendar_lang='en',
                                         format='%Y-%m-%d',
                                         default='',
                                         button_text='Changed since this date',
                                         validator=validators.DateTimeConverter(format="%Y-%m-%d"))


#################################################################################
#
# generate the module search form
#
modsearch_form = widgets.TableForm(name='modsearch_form',
                                fields=ModuleSearchFields(),
                                submit_text="Find modules",
                                action="searchyangdb_mod")


#################################################################################
#
# generate the typedef search form
#
typsearch_form = widgets.TableForm(name='typsearch_form',
                                fields=TypedefSearchFields(),
                                submit_text="Find types",
                                action="searchyangdb_typ")

#################################################################################
#
# generate the object search form
#
objsearch_form = widgets.TableForm(name='objsearch_form',
                                fields=ObjectSearchFields(),
                                submit_text="Find objects",
                                action="searchyangdb_obj")

#################################################################################
#
# generate the type name usage search form
#
tusearch_form = widgets.TableForm(name='tusearch_form',
                                  fields=TypeUsageSearchFields(),
                                  submit_text="Find objects using this type",
                                  action="searchyangdb_tu")


#################################################################################
#
# generate the extension search form
#
extsearch_form = widgets.TableForm(name='extsearch_form',
                                  fields=ExtensionSearchFields(),
                                  submit_text="Find extensions",
                                  action="searchyangdb_ext")


#################################################################################
# main entry point
class Root(controllers.RootController):

    registration = reg_controllers.UserRegistration()

    quickmod = NcquickmodController.NcquickmodController()

    @expose(template="nc.templates.welcome")
    # @identity.require(identity.in_group("admin"))
    def index(self):
        import time
        # log.debug("Happy TurboGears Controller Responding For Duty")
        flash("Your application is now running")
        return dict(now=time.ctime())

    @expose(template="nc.templates.registration.login")
    def login(self, forward_url=None, *args, **kw):

        if forward_url:
            if isinstance(forward_url, list):
                forward_url = forward_url.pop(0)
            else:
                del request.params['forward_url']

        if not identity.current.anonymous and identity.was_login_attempted() \
                and not identity.get_identity_errors():
            redirect(tg.url(forward_url or '/', kw))

        if identity.was_login_attempted():
            msg = _("The credentials you supplied were not correct or "
                   "did not grant access to this resource.")
        elif identity.get_identity_errors():
            msg = _("You must provide your credentials before accessing "
                   "this resource.")
        else:
            msg = _("Please log in.")
            if not forward_url:
                forward_url = request.headers.get("Referer", "/")

        response.status = 401
        return dict(logging_in=True, message=msg,
            forward_url=forward_url, previous_url=request.path_info,
            original_parameters=request.params)

    @expose()
    def logout(self):
        identity.current.logout()
        redirect("/")


    #################################################################################
    #
    # Home Page
    #
    @expose(template="nc.templates.homepage")
    def index(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=1)


    #################################################################################
    #
    # Unknown Page
    #
    @expose(template="nc.templates.unknown")
    def default(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=0)


    #################################################################################
    #
    # List Pages
    #
    @expose(template="nc.templates.ncmodule_list")
    def modulelist(self, *args, **kw):
        ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1", 
                                        Ncmodule.q.islatest=="1"),
                                    orderBy=Ncmodule.q.modname)
        return dict(modmenu=moduleJumpMenu,
                    ncmodules=ncmodules,
                    copyright=0)


    @expose(template="nc.templates.nctypedef_list")
    def typedeflist(self,  mod=None, *args, **kw):
        if mod:
            nctypedefs = Nctypedef.select(AND(Nctypedef.q.parenttypename=="", 
                                              Nctypedef.q.islatest=="1",
                                              Nctypedef.q.modname==mod),
                                          orderBy=Nctypedef.q.name)
        else:
            nctypedefs = Nctypedef.select(AND(Nctypedef.q.parenttypename=="", 
                                              Nctypedef.q.islatest=="1"),
                                          orderBy=Nctypedef.q.name)
        return dict(modmenu=moduleJumpMenu,
                    nctypedefs=nctypedefs,
                    mod=mod,
                    copyright=0)


    @expose(template="nc.templates.ncgrouping_list")
    def groupinglist(self,  mod=None, *args, **kw):
        if mod:
            ncgroupings = Ncgrouping.select(AND(Ncgrouping.q.islatest=="1",
                                                Ncgrouping.q.modname==mod),
                                            orderBy=Ncgrouping.q.name)
        else:
            ncgroupings = Ncgrouping.select(Ncgrouping.q.islatest=="1",
                                            orderBy=Ncgrouping.q.name)
        return dict(modmenu=moduleJumpMenu,
                    ncgroupings=ncgroupings,
                    mod=mod,
                    copyright=0)


    @expose(template="nc.templates.ncobject_list")
    def objectlist(self,  mod=None, *args, **kw):
        if mod:
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.istop=="1",
                    Ncobject.q.isdata=="1",
                    Ncobject.q.modname==mod),
                orderBy=Ncobject.q.objectid)
        else:
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.istop=="1",
                    Ncobject.q.isdata=="1"),
                orderBy=Ncobject.q.objectid)

        return dict(modmenu=moduleJumpMenu,
                    ncobjects=ncobjects,
                    mod=mod,
                    copyright=0)


    @expose(template="nc.templates.ncrpc_list")
    def rpclist(self,  mod=None, *args, **kw):
        if mod:
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.objtyp=="rpc",
                    Ncobject.q.modname==mod),
                orderBy=Ncobject.q.name)
        else:
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.objtyp=="rpc"),
                orderBy=Ncobject.q.name)

        return dict(modmenu=moduleJumpMenu,
                    ncobjects=ncobjects,
                    mod=mod,
                    copyright=0)


    @expose(template="nc.templates.ncnotif_list")
    def notificationlist(self, mod=None, *args, **kw):
        if mod:
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.objtyp=="notification",
                    Ncobject.q.modname==mod),
                orderBy=Ncobject.q.name)
        else:
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.objtyp=="notification"),
                orderBy=Ncobject.q.name)

        return dict(modmenu=moduleJumpMenu,
                    ncobjects=ncobjects,
                    mod=mod,
                    copyright=0)


    @expose(template="nc.templates.ncextension_list")
    def extensionlist(self,  mod=None, *args, **kw):
        if mod:
            ncextensions = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                  Ncextension.q.modname==mod),
                                              orderBy=Ncextension.q.name)
        else:
            ncextensions = Ncextension.select(Ncextension.q.islatest=="1",
                                              orderBy=Ncextension.q.name)

        return dict(modmenu=moduleJumpMenu,
                    ncextensions=ncextensions,
                    mod=mod,
                    copyright=0)



    #################################################################################
    #
    # Browse Pages
    #
    @expose(template="nc.templates.ncmodule_browse")
    def modulebrowse(self, mod="", *args, **kw):
        tabber = widgets.Tabber()

        if mod=="":
            ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1", 
                                            Ncmodule.q.islatest=="1"),
                                        orderBy=Ncmodule.q.modname)

        else:
            ncmodules = Ncmodule.select(AND(Ncmodule.q.modname==mod,
                                            Ncmodule.q.ismod=="1", 
                                            Ncmodule.q.islatest=="1"),
                                        orderBy=Ncmodule.q.modname)

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber, 
                    ncmodules=ncmodules,
                    mod=mod,
                    copyright=0)


    @expose(template="nc.templates.nctypedef_browse")
    def typedefbrowse(self, mod="", name="", *args, **kw):
        tabber = widgets.Tabber()

        if mod=="" and name=="":
            nctypedefs = Nctypedef.select(AND(Nctypedef.q.parenttypename=="", 
                                              Nctypedef.q.islatest=="1"),
                                          orderBy=Nctypedef.q.name)

        if mod!="" and name=="":
            nctypedefs = Nctypedef.select(AND(Nctypedef.q.modname==mod,
                                              Nctypedef.q.parenttypename=="",
                                              Nctypedef.q.islatest=="1"),
                                            orderBy=Nctypedef.q.name)

        if (mod!="" and name!=""):
            nctypedefs = Nctypedef.select(AND(Nctypedef.q.modname==mod,
                                              Nctypedef.q.name==name,
                                              Nctypedef.q.parenttypename=="",
                                              Nctypedef.q.islatest=="1"),
                                          orderBy=Nctypedef.q.name)

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber, 
                    nctypedefs=nctypedefs,
                    mod=mod,
                    name=name,
                    copyright=0)


    @expose(template="nc.templates.ncgrouping_browse")
    def groupingbrowse(self,  mod="", name="", *args, **kw):
        tabber = widgets.Tabber()
        if mod=="" and name=="":
            ncgroupings = Ncgrouping.select(Ncgrouping.q.islatest=="1",
                                            orderBy=Ncgrouping.q.name)

        if mod!="" and name=="":
            ncgroupings = Ncgrouping.select(AND(Ncgrouping.q.modname==mod,
                                                Ncgrouping.q.islatest=="1"),
                                            orderBy=Ncgrouping.q.name)

        if mod!="" and name!="":
            ncgroupings = Ncgrouping.select(AND(Ncgrouping.q.modname==mod,
                                                Ncgrouping.q.islatest=="1",
                                                Ncgrouping.q.name==name),
                                            orderBy=Ncgrouping.q.name)

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber, 
                    ncgroupings=ncgroupings,
                    mod=mod,
                    name=name,
                    copyright=0)


    @expose(template="nc.templates.ncobject_browse")
    def objectbrowse(self,  mod="", name="", *args, **kw):
        tabber = widgets.Tabber()
        if mod=="" and name=="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.istop=="1",
                    Ncobject.q.isdata=="1"),
                orderBy=Ncobject.q.objectid)

        if mod!="" and name=="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.istop=="1",
                    Ncobject.q.isdata=="1",
                    Ncobject.q.modname==mod),
                orderBy=Ncobject.q.objectid)

        if mod!="" and name!="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.istop=="1",
                    Ncobject.q.isdata=="1",
                    Ncobject.q.modname==mod,
                    Ncobject.q.name==name),
                orderBy=Ncobject.q.objectid)

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber, 
                    ncobjects=ncobjects,
                    mod=mod,
                    name=name,
                    copyright=0)


    @expose(template="nc.templates.ncrpc_browse")
    def rpcbrowse(self, mod="", name="", *args, **kw):
        tabber = widgets.Tabber()
        if mod=="" and name=="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.objtyp=="rpc"),
                orderBy=Ncobject.q.name)

        if mod!="" and name=="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.objtyp=="rpc",
                    Ncobject.q.modname==mod),
                orderBy=Ncobject.q.name)

        if mod!="" and name!="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.objtyp=="rpc", 
                    Ncobject.q.modname==mod,
                    Ncobject.q.name==name),
                orderBy=Ncobject.q.name)

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber, 
                    ncobjects=ncobjects,
                    mod=mod,
                    name=name,
                    copyright=0)


    @expose(template="nc.templates.ncnotif_browse")
    def notificationbrowse(self, mod="", name="", *args, **kw):
        tabber = widgets.Tabber()
        if mod=="" and name=="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.objtyp=="notification"),
                orderBy=Ncobject.q.name)

        if mod!="" and name=="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.modname==mod,
                    Ncobject.q.objtyp=="notification"),
                orderBy=Ncobject.q.name)

        if mod!="" and name!="":
            ncobjects = Ncobject.select(
                AND(Ncobject.q.islatest=="1",
                    Ncobject.q.modname==mod,
                    Ncobject.q.objtyp=="notification", 
                    Ncobject.q.name==name),
                orderBy=Ncobject.q.name)

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber, 
                    ncobjects=ncobjects,
                    mod=mod,
                    name=name,
                    ccopyright=0)


    @expose(template="nc.templates.ncextension_browse")
    def extensionbrowse(self, mod="", name="", *args, **kw):
        tabber = widgets.Tabber()
        if mod=="" and name=="":
            ncextensions = Ncextension.select(Ncextension.q.islatest=="1",
                                              orderBy=Ncextension.q.name)
        if mod!="" and name=="":
            ncextensions = Ncextension.select(
                AND(Ncextension.q.islatest=="1",
                    Ncextension.q.modname==mod),
                orderBy=Ncextension.q.name)

        if mod!="" and name!="":
            ncextensions = Ncextension.select(
                AND(Ncextension.q.islatest=="1", 
                    Ncextension.q.modname==mod,
                    Ncextension.q.name==name),
                orderBy=Ncextension.q.name)

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber, 
                    ncextensions=ncextensions,
                    mod=mod,
                    name=name,
                    copyright=0)


    #################################################################################
    #
    # Full Module Report
    #
    @expose(template="nc.templates.ncmodule_report")
    def modulereport(self, mod, version="latest", *args, **kw):
        tabber = widgets.Tabber()

        if version=="latest":
            ncmodules = Ncmodule.select(AND(Ncmodule.q.modname==mod, 
                                            Ncmodule.q.islatest=="1"),
                                        orderBy=Ncmodule.q.modname)
            nctypedefs = Nctypedef.select(AND(Nctypedef.q.modname==mod, 
                                          Nctypedef.q.islatest=="1"),
                                          orderBy=Nctypedef.q.name)
            ncgroupings = Ncgrouping.select(AND(Ncgrouping.q.modname==mod, 
                                                Ncgrouping.q.islatest=="1"),
                                            orderBy=Ncgrouping.q.name)
            ncobjects = Ncobject.select(AND(Ncobject.q.modname==mod,
                                            Ncobject.q.islatest=="1",
                                            Ncobject.q.isdata=="1"),
                                        orderBy=Ncobject.q.objectid)
            ncrpcs = Ncobject.select(AND(Ncobject.q.modname==mod, 
                                         Ncobject.q.islatest=="1",
                                         Ncobject.q.objtyp=="rpc"),
                                     orderBy=Ncobject.q.name)
            ncnotifs = Ncobject.select(AND(Ncobject.q.modname==mod, 
                                           Ncobject.q.islatest=="1",
                                           Ncobject.q.objtyp=="notification"),
                                       orderBy=Ncobject.q.name)
            ncextensions = Ncextension.select(AND(Ncextension.q.modname==mod,
                                                  Ncextension.q.islatest=="1"),
                                              orderBy=Ncextension.q.name)

        else:
            ncmodules = Ncmodule.select(AND(Ncmodule.q.modname==mod,
                                            Ncmodule.q.version==version),
                                        orderBy=Ncmodule.q.modname)
            nctypedefs = Nctypedef.select(AND(Nctypedef.q.modname==mod,
                                          Nctypedef.q.version==version),
                                          orderBy=Nctypedef.q.name)
            ncgroupings = Ncgrouping.select(AND(Ncgrouping.q.modname==mod, 
                                                Ncgrouping.q.islatest==version),
                                            orderBy=Ncgrouping.q.name)
            ncobjects = Ncobject.select(AND(Ncobject.q.modname==mod,
                                            Ncobject.q.version==version,
                                            Ncobject.q.isdata=="1"),
                                        orderBy=Ncobject.q.objectid)
            ncrpcs = Ncobject.select(AND(Ncobject.q.modname==mod, 
                                         Ncobject.q.version==version,
                                         Ncobject.q.objtyp=="rpc"),
                                     orderBy=Ncobject.q.name)
            ncnotifs = Ncobject.select(AND(Ncobject.q.modname==mod, 
                                           Ncobject.q.versiont==version,
                                           Ncobject.q.objtyp=="notification"),
                                       orderBy=Ncobject.q.name)
            ncextensions = \
                Ncextension.select(AND(Ncextension.q.modname==mod,
                                       Ncextension.q.version==version),
                                   orderBy=Ncextension.q.name)

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber, 
                    ncmodules=ncmodules,
                    nctypedefs=nctypedefs,
                    ncgroupings=ncgroupings,
                    ncobjects=ncobjects,
                    ncrpcs=ncrpcs,
                    ncnotifs=ncnotifs,
                    ncextensions=ncextensions,
                    mod=mod,
                    version=version,
                    copyright=0)


    #################################################################################
    #
    # Show module source page
    # generated with yangdump -f html
    @expose(template="nc.templates.ncmodule_source")
    def modules(self, mod, version, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    mod=mod,
                    version=version,
                    copyright=0)
                    

    #################################################################################
    #
    # Run Yangdump page
    #
    @expose(template="nc.templates.run_yangdump")
    def run_yangdump(self, *args, **kw):

        return dict(modmenu=moduleJumpMenu,
                    form=runyangdump_form,
                    copyright=0)


    @expose(template="nc.templates.yangdump_results")
    def yangdumpresults(self, srcfile, resfile, report, *args, **kw):

        return dict(modmenu=moduleJumpMenu,
                    srcfile=srcfile,
                    resfile=resfile,
                    report=report,
                    copyright=0)


    #################################################################################
    #
    # Process run yangdump parameters
    #
    @expose()
    @validate(form=runyangdump_form)
    @error_handler(run_yangdump)
    def runyangdump(self, srcfile, depfiles=None, 
                    modversion=False, exports=False,
                    dependencies=False, identifiers=False, **kw):
        """Handle submission from the runyang form"""

        report = False
        result = deleteOldYangFiles()
        if result != 0:
            flash(result)
            redirect('/')

        result = copyYangFile(srcfile.filename, srcfile.file)
        if result != "":
            flash(result)
            redirect('/')

        if depfiles:
            for depfile in depfiles:
                dep = depfile['depfile']
                if dep.filename:
                    result = copyYangFile(dep.filename, dep.file)
                    if result != "":
                        flash(result)
                        redirect('/')

        # setup the command line to call yangdump
        logfile = getYangLogFilename()
        infile = getYangInputFilename(srcfile.filename)
        modpath = getYangModpath()
        cmdline = "/usr/bin/yangdump --log-level=info --log=" + logfile \
            + " --modpath=" + modpath + " --module=" + infile

        if modversion:
            cmdline += " --modversion"
            report = True

        if exports:
            cmdline += " --exports"
            report = True

        if dependencies:
            cmdline += " --dependencies"
            report = True

        if identifiers:
            cmdline += " --identifiers"
            report = True

        if report:
            cmdline += " --output="
            cmdline += getYangOutputFilename()

        log.debug("run yangdump: " + cmdline)

        yang_result = os.system(cmdline)

        newpath = getYangResultFilename(srcfile.filename)
        redirect(newpath, report=report)



    #################################################################################
    #
    # Run Yangdiff page
    #
    @expose(template="nc.templates.run_yangdiff")
    def run_yangdiff(self, *args, **kw):

        return dict(modmenu=moduleJumpMenu,
                    form=runyangdiff_form,
                    copyright=0)


    @expose(template="nc.templates.yangdiff_results")
    def yangdiffresults(self, srcfile, resfile, report, *args, **kw):

        return dict(modmenu=moduleJumpMenu,
                    srcfile=srcfile,
                    resfile=resfile,
                    report=report,
                    copyright=0)


    #################################################################################
    #
    # Process run yangdiff parameters
    #
    @expose()
    @validate(form=runyangdiff_form)
    @error_handler(run_yangdiff)
    def runyangdiff(self, oldfile, newfile, depfiles=None, **kw):
        """Handle submission from the rundiff form"""

        result = deleteOldYangFiles()
        if result != 0:
            flash(result)
            redirect('/')

        result = copyYangFile(oldfile.filename, oldfile.file)
        if result != "":
            flash(result)
            redirect('/')


        result = copyYangFile(newfile.filename, newfile.file)
        if result != "":
            flash(result)
            redirect('/')

        if depfiles:
            for depfile in depfiles:
                dep = depfile['depfile']
                if dep.filename:
                    result = copyYangFile(dep.filename, dep.file)
                    if result != "":
                        flash(result)
                        redirect('/')

        # setup the command line to call yangdump
        logfile = getYangLogFilename()
        ofile = getYangInputFilename(oldfile.filename)
        nfile = getYangInputFilename(newfile.filename)
        modpath = getYangModpath()
        cmdline = "/usr/bin/yangdiff --log-level=info --log=" + logfile \
            + " --modpath=" + modpath + " --old=" + ofile + " --new=" + nfile + " --output="

        cmdline += getYangOutputFilename()

        log.debug("run yangdiff: " + cmdline)

        yang_result = os.system(cmdline)

        newpath = getYangResultFilename(oldfile.filename)
        redirect(newpath, report=True)



    #################################################################################
    #
    # Search database page
    #

    @expose(template="nc.templates.search")
    def search(self, *args, **kw):
        tabber = widgets.Tabber()

        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber,
                    modform=modsearch_form,
                    typform=typsearch_form,
                    objform=objsearch_form,
                    tuform=tusearch_form,
                    extform=extsearch_form,
                    copyright=0)


    #################################################################################
    #
    # Process module search parameters
    #
    expose()
    @validate(form=modsearch_form)
    @error_handler(search)
    def searchyangdb_mod(self, matchtype, modnamepart=None,
                         modprefix=None, moddate=None, **data):
        """Generate database search results"""

        # have parameters, now check if any parameters were entered
        if modnamepart == None and modprefix == None and moddate == None:
            redirect('/search')

        redirect('/modsearch_results',
                 matchtype=matchtype,
                 modnamepart=modnamepart,
                 modprefix=modprefix,
                 moddate=moddate)


    #################################################################################
    #
    # generate module search results page
    #
    @expose(template="nc.templates.modsearch_results")
    def modsearch_results(self, 
                          matchtype,
                          modnamepart=None, 
                          modprefix=None,
                          moddate=None,
                          *args, **kw):

        # remove 1 independent variable, set to 'start' if not provided
        if moddate:
            moddateset = True
        else:
            moddate = '1900-01-01'
            moddateset = False

        if matchtype=='All':
            if modnamepart==None and modprefix==None:
                ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                Ncmodule.q.islatest=="1",
                                                Ncmodule.q.version >= moddate),
                                            orderBy=Ncmodule.q.modname)
            if modnamepart and modprefix==None:
                ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                Ncmodule.q.islatest=="1",
                                                CONTAINSSTRING(Ncmodule.q.modname, modnamepart),
                                                Ncmodule.q.version >= moddate),
                                            orderBy=Ncmodule.q.modname)
            if modnamepart==None and modprefix:
                ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                Ncmodule.q.islatest=="1",
                                                Ncmodule.q.modprefix==modprefix,
                                                Ncmodule.q.version >= moddate),
                                            orderBy=Ncmodule.q.modname)
            if modnamepart and modprefix:
                ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                Ncmodule.q.islatest=="1",
                                                CONTAINSSTRING(Ncmodule.q.modname, modnamepart),
                                                Ncmodule.q.modprefix==modprefix,
                                                Ncmodule.q.version >= moddate),
                                            orderBy=Ncmodule.q.modname)

        else:
            if modnamepart==None and modprefix==None:
                ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                Ncmodule.q.islatest=="1",
                                                Ncmodule.q.version >= moddate),
                                            orderBy=Ncmodule.q.modname)
            if modnamepart and modprefix==None:
                if moddateset==True:
                    ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                    Ncmodule.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncmodule.q.modname, 
                                                                      modnamepart),
                                                       Ncmodule.q.version >= moddate)),
                                                orderBy=Ncmodule.q.modname)
                else:
                    ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                    Ncmodule.q.islatest=="1",
                                                    CONTAINSSTRING(Ncmodule.q.modname, 
                                                                   modnamepart)),
                                                orderBy=Ncmodule.q.modname)
            if modnamepart==None and modprefix:
                if moddateset==True:
                    ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                    Ncmodule.q.islatest=="1",
                                                    OR(Ncmodule.q.modprefix==modprefix,
                                                       Ncmodule.q.version >= moddate)),
                                                orderBy=Ncmodule.q.modname)
                else:
                    ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                    Ncmodule.q.islatest=="1",
                                                    Ncmodule.q.modprefix==modprefix),
                                                orderBy=Ncmodule.q.modname)
            if modnamepart and modprefix:
                if moddateset==True:
                    ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                    Ncmodule.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncmodule.q.modname,
                                                                      modnamepart),
                                                       Ncmodule.q.modprefix==modprefix,
                                                       Ncmodule.q.version >= moddate)),
                                                orderBy=Ncmodule.q.modname)
                else:
                    ncmodules = Ncmodule.select(AND(Ncmodule.q.ismod=="1",
                                                    Ncmodule.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncmodule.q.modname,
                                                                      modnamepart),
                                                       Ncmodule.q.modprefix==modprefix)),
                                                orderBy=Ncmodule.q.modname)

        return dict(modmenu=moduleJumpMenu,
                    ncmodules=ncmodules,
                    copyright=0)

    #################################################################################
    #
    # Process typedef search parameters
    #
    @expose()
    @validate(form=typsearch_form)
    @error_handler(search)
    def searchyangdb_typ(self, matchtype, modnamepart=None,
                         typnamepart=None, moddate=None, **data):
        """Generate database search results"""

        # have parameters, now check if any parameters were entered
        if modnamepart == None and typnamepart == None and moddate == None:
            redirect('/search')

        redirect('/typsearch_results',
                 matchtype=matchtype,
                 modnamepart=modnamepart,
                 typnamepart=typnamepart,
                 moddate=moddate)

    #################################################################################
    #
    # Generate typedef search results page
    #
    @expose(template="nc.templates.typsearch_results")
    def typsearch_results(self, 
                          matchtype,
                          modnamepart=None, 
                          typnamepart=None,
                          moddate=None,
                          *args, **kw):

        # remove 1 independent variable, set to 'start' if not provided
        if moddate:
            moddateset = True
        else:
            moddate = '1900-01-01'
            moddateset = False

        if matchtype=='All':
            if modnamepart==None and typnamepart==None:
                nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                  Nctypedef.q.version >= moddate),
                                              orderBy=Nctypedef.q.name)
            if modnamepart and typnamepart==None:
                nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                  CONTAINSSTRING(Nctypedef.q.modname, modnamepart),
                                                  Nctypedef.q.version >= moddate),
                                              orderBy=Nctypedef.q.name)
            if modnamepart==None and typnamepart:
                nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                  CONTAINSSTRING(Nctypedef.q.name, typnamepart),
                                                  Nctypedef.q.version >= moddate),
                                              orderBy=Nctypedef.q.name)
            if modnamepart and typnamepart:
                nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                  CONTAINSSTRING(Nctypedef.q.modname, modnamepart),
                                                  CONTAINSSTRING(Nctypedef.q.name, typnamepart),
                                                  Nctypedef.q.version >= moddate),
                                              orderBy=Nctypedef.q.name)

        else:
            if modnamepart==None and typnamepart==None:
                nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                  Nctypedef.q.version >= moddate),
                                              orderBy=Nctypedef.q.name)
            if modnamepart and typnamepart==None:
                if moddateset==True:
                    nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                      OR(CONTAINSSTRING(Nctypedef.q.modname, 
                                                                        modnamepart),
                                                         Nctypedef.q.version >= moddate)),
                                                  orderBy=Nctypedef.q.name)
                else:
                    nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                      CONTAINSSTRING(Nctypedef.q.modname, 
                                                                     modnamepart)),
                                                  orderBy=Nctypedef.q.name)
            if modnamepart==None and typnamepart:
                if moddateset==True:
                    nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                      OR(CONTAINSSTRING(Nctypedef.q.name,
                                                                        typnamepart),
                                                         Nctypedef.q.version >= moddate)),
                                                  orderBy=Nctypedef.q.name)
                else:
                    nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                      CONTAINSSTRING(Nctypedef.q.name, typnamepart)),
                                                  orderBy=Nctypedef.q.name)
            if modnamepart and typnamepart:
                if moddateset==True:
                    nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                      OR(CONTAINSSTRING(Nctypedef.q.modname,
                                                                        modnamepart),
                                                         CONTAINSSTRING(Nctypedef.q.name, 
                                                                        typnamepart),
                                                         Nctypedef.q.version >= moddate)),
                                                  orderBy=Nctypedef.q.name)
                else:
                    nctypedefs = Nctypedef.select(AND(Nctypedef.q.islatest=="1",
                                                      OR(CONTAINSSTRING(Nctypedef.q.modname,
                                                                        modnamepart),
                                                         CONTAINSSTRING(Nctypedef.q.name, 
                                                                        typnamepart))),
                                                  orderBy=Nctypedef.q.name)

        return dict(modmenu=moduleJumpMenu,
                    nctypedefs=nctypedefs,
                    copyright=0)


    #################################################################################
    #
    # Process object search parameters
    #
    @expose()
    @validate(form=objsearch_form)
    @error_handler(search)
    def searchyangdb_obj(self, matchtype, modnamepart=None,
                         objnamepart=None, moddate=None, **data):
        """Generate database search results"""

        # have parameters, now check if any parameters were entered
        if modnamepart==None and objnamepart==None and moddate==None:
            redirect('/search')

        redirect('/objsearch_results',
                 matchtype=matchtype,
                 modnamepart=modnamepart,
                 objnamepart=objnamepart,
                 moddate=moddate)


    #################################################################################
    #
    # Generate object search results page
    #
    @expose(template="nc.templates.objsearch_results")
    def objsearch_results(self, 
                          matchtype,
                          modnamepart=None, 
                          objnamepart=None,
                          moddate=None,
                          *args, **kw):

        # remove 1 independent variable, set to 'start' if not provided
        if moddate:
            moddateset = True
        else:
            moddate = '1900-01-01'
            moddateset = False

        if matchtype=='All':
            if modnamepart==None and objnamepart==None:
                ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                Ncobject.q.version >= moddate),
                                            orderBy=Ncobject.q.objectid)
            if modnamepart and objnamepart==None:
                ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                CONTAINSSTRING(Ncobject.q.modname, modnamepart),
                                                Ncobject.q.version >= moddate),
                                            orderBy=Ncobject.q.objectid)
            if modnamepart==None and objnamepart:
                ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                CONTAINSSTRING(Ncobject.q.name, objnamepart),
                                                Ncobject.q.version >= moddate),
                                            orderBy=Ncobject.q.objectid)
            if modnamepart and objnamepart:
                ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                CONTAINSSTRING(Ncobject.q.modname, modnamepart),
                                                CONTAINSSTRING(Ncobject.q.name, objnamepart),
                                                Ncobject.q.version >= moddate),
                                            orderBy=Ncobject.q.objectid)
        else:
            if modnamepart==None and objnamepart==None:
                ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                Ncobject.q.version >= moddate),
                                            orderBy=Ncobject.q.objectid)
            if modnamepart and objnamepart==None:
                if moddateset==True:
                    ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncobject.q.modname, 
                                                                      modnamepart),
                                                       Ncobject.q.version >= moddate)),
                                                orderBy=Ncobject.q.objectid)
                else:
                    ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                    CONTAINSSTRING(Ncobject.q.modname, 
                                                                   modnamepart)),
                                                orderBy=Ncobject.q.objectid)
            if modnamepart==None and objnamepart:
                if moddateset==True:
                    ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncobject.q.name,
                                                                      objnamepart),
                                                       Ncobject.q.version >= moddate)),
                                                orderBy=Ncobject.q.objectid)
                else:
                    ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                    CONTAINSSTRING(Ncobject.q.name,
                                                                   objnamepart)),
                                                  orderBy=Ncobject.q.objectid)
            if modnamepart and objnamepart:
                if moddateset==True:
                    ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncobject.q.modname,
                                                                      modnamepart),
                                                       CONTAINSSTRING(Ncobject.q.name, 
                                                                      objnamepart),
                                                       Ncobject.q.version >= moddate)),
                                                orderBy=Ncobject.q.objectid)
                else:
                    ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncobject.q.modname,
                                                                      modnamepart),
                                                       CONTAINSSTRING(Ncobject.q.name, 
                                                                      objnamepart))),
                                                orderBy=Ncobject.q.objectid)

        return dict(modmenu=moduleJumpMenu,
                    ncobjects=ncobjects,
                    copyright=0)


    #################################################################################
    #
    # Process type name search parameters
    #
    @expose()
    @validate(form=tusearch_form)
    @error_handler(search)
    def searchyangdb_tu(self, matchtype, typnamepart, **data):
        """Generate database search results"""

        # have parameters, now check if any parameters were entered
        if typnamepart==None:
            redirect('/search')

        redirect('/tusearch_results', 
                 matchtype=matchtype,
                 typnamepart=typnamepart)


    #################################################################################
    #
    # Generate type name usage search results page
    #
    @expose(template="nc.templates.tusearch_results")
    def tusearch_results(self, matchtype, typnamepart, *args, **kw):

        ncobjects = None

        if matchtype=='Contains':
            ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                            CONTAINSSTRING(Ncobject.q.typename, typnamepart),
                                            Ncobject.q.objtyp!="uses"),
                                        orderBy=Ncobject.q.objectid)
            
        if matchtype=='Exact':
            ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                            Ncobject.q.typename==typnamepart,
                                            Ncobject.q.objtyp!="uses"),
                                        orderBy=Ncobject.q.objectid)

        if matchtype=='Starts with':
            ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                            Ncobject.q.typename.startswith(typnamepart),
                                            Ncobject.q.objtyp!="uses"),
                                        orderBy=Ncobject.q.objectid)


        if matchtype=='Ends with':
            ncobjects = Ncobject.select(AND(Ncobject.q.islatest=="1",
                                            Ncobject.q.typename.endswith(typnamepart),
                                            Ncobject.q.objtyp!="uses"),
                                        orderBy=Ncobject.q.objectid)

        return dict(modmenu=moduleJumpMenu,
                    ncobjects=ncobjects,
                    copyright=0)


    #################################################################################
    #
    # Process extension search parameters
    #
    @expose()
    @validate(form=extsearch_form)
    @error_handler(search)
    def searchyangdb_ext(self, matchtype, modnamepart=None,
                         extnamepart=None, moddate=None, **data):
        """Generate database search results"""

        # have parameters, now check if any parameters were entered
        if modnamepart==None and extnamepart==None and moddate==None:
            redirect('/search')

        redirect('/extsearch_results',
                 matchtype=matchtype,
                 modnamepart=modnamepart,
                 extnamepart=extnamepart,
                 moddate=moddate)

    #################################################################################
    #
    # Generate extension search results page
    #
    @expose(template="nc.templates.extsearch_results")
    def extsearch_results(self, 
                          matchtype,
                          modnamepart=None, 
                          extnamepart=None,
                          moddate=None,
                          *args, **kw):

        # remove 1 independent variable, set to 'start' if not provided
        if moddate:
            moddateset = True
        else:
            moddate = '1900-01-01'
            moddateset = False

        if matchtype=='All':
            if modnamepart==None and extnamepart==None:
                ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                Ncextension.q.version >= moddate),
                                            orderBy=Ncextension.q.name)
            if modnamepart and extnamepart==None:
                ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                CONTAINSSTRING(Ncextension.q.modname, modnamepart),
                                                Ncextension.q.version >= moddate),
                                            orderBy=Ncextension.q.name)
            if modnamepart==None and extnamepart:
                ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                CONTAINSSTRING(Ncextension.q.name, extnamepart),
                                                Ncextension.q.version >= moddate),
                                            orderBy=Ncextension.q.name)
            if modnamepart and extnamepart:
                ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                CONTAINSSTRING(Ncextension.q.modname, modnamepart),
                                                CONTAINSSTRING(Ncextension.q.name, extnamepart),
                                                Ncextension.q.version >= moddate),
                                            orderBy=Ncextension.q.name)
        else:
            if modnamepart==None and extnamepart==None:
                ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                Ncextension.q.version >= moddate),
                                            orderBy=Ncextension.q.name)
            if modnamepart and extnamepart==None:
                if moddateset==True:
                    ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncextension.q.modname, 
                                                                      modnamepart),
                                                       Ncextension.q.version >= moddate)),
                                                orderBy=Ncextension.q.name)
                else:
                    ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                    CONTAINSSTRING(Ncextension.q.modname, 
                                                                   modnamepart)),
                                                orderBy=Ncextension.q.name)
            if modnamepart==None and extnamepart:
                if moddateset==True:
                    ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncextension.q.name,
                                                                      extnamepart),
                                                       Ncextension.q.version >= moddate)),
                                                orderBy=Ncextension.q.name)
                else:
                    ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                    CONTAINSSTRING(Ncextension.q.name,
                                                                   extnamepart)),
                                                  orderBy=Ncextension.q.name)
            if modnamepart and extnamepart:
                if moddateset==True:
                    ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncextension.q.modname,
                                                                      modnamepart),
                                                       CONTAINSSTRING(Ncextension.q.name, 
                                                                      extnamepart),
                                                       Ncextension.q.version >= moddate)),
                                                orderBy=Ncextension.q.name)
                else:
                    ncexts = Ncextension.select(AND(Ncextension.q.islatest=="1",
                                                    OR(CONTAINSSTRING(Ncextension.q.modname,
                                                                      modnamepart),
                                                       CONTAINSSTRING(Ncextension.q.name, 
                                                                      extnamepart))),
                                                orderBy=Ncextension.q.name)

        return dict(modmenu=moduleJumpMenu,
                    ncexts=ncexts,
                    copyright=0)



    #################################################################################
    #
    # Show Yangdump manual page
    #
    @expose(template="nc.templates.man_yangdump")
    def yangdump_manual(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=0)

    #################################################################################
    #
    # Show Yangdiff manual page
    #
    @expose(template="nc.templates.man_yangdiff")
    def yangdiff_manual(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=0)


    #################################################################################
    #
    # Show the YANG database documentation page
    #
    @expose(template="nc.templates.doc_database")
    def database_docs(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=0)


    #################################################################################
    #
    # Show the NETCONF documentation page
    #
    @expose(template="nc.templates.doc_netconf")
    def netconf_docs(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=0)


    #################################################################################
    #
    # Show the YANG documentation page
    #
    @expose(template="nc.templates.doc_yang")
    def yang_docs(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=0)

    #################################################################################
    #
    # Show the YANG automation page
    #
    @expose(template="nc.templates.doc_yangauto")
    def yang_auto(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=0)

    #################################################################################
    #
    # Show the download page
    #
    @expose(template="nc.templates.download")
    def download(self, *args, **kw):
        tabber = widgets.Tabber()
        return dict(modmenu=moduleJumpMenu,
                    tabber=tabber,
                    copyright=0)

    #################################################################################
    #
    # test page
    #
    @expose(template="nc.templates.jtest")
    def jtest(self, *args, **kw):
        return dict(modmenu=moduleJumpMenu,
                    copyright=0)
