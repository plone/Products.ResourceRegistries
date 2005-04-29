from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Acquisition import aq_base, aq_parent, aq_inner

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import IJSRegistry

from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext

from OFS.Image import File
from DateTime import DateTime

import random


class JSRegistryTool(UniqueObject, SimpleItem, PropertyManager):
    """ A Plone registry for managing the linking to Javascript files.
    """

    id = config.JSTOOLNAME
    meta_type = config.JSTOOLTYPE
    title = "JavaScript Registry"

    security = ClassSecurityInfo()

    __implements__ = (SimpleItem.__implements__, IJSRegistry,)

    # ZMI stuff
    manage_jsForm = PageTemplateFile('www/jsconfig', config.GLOBALS)
    manage_jsComposition = PageTemplateFile('www/jscomposition', config.GLOBALS)



    manage_options=(
        ({ 'label'  : 'Javascript Registry',
           'action' : 'manage_jsForm',
           },
        { 'label'  : 'Merged JS Composition',
           'action' : 'manage_jsComposition',
           }
         ) + SimpleItem.manage_options
        )


    def __init__(self ):
        """ add the storages """
        self.scripts = ()
        self.cookedscripts = ()
        self.concatenatedscripts = {}


    security.declareProtected(permissions.ManagePortal, 'registerScript')
    def registerScript(self, id, expression='', inline=False, enabled=True):
        """ register a script"""
        script = {}
        script['id'] = id
        script['expression'] = expression
        script['inline'] = inline
        script['enabled'] = enabled
        self.storeScript(script)


    security.declarePrivate('validateId')
    def validateId(self, id, existing):
        """ safeguard against dulicate ids"""
        for sheet in existing:
            if sheet.get('id') == id:
                raise ValueError, 'Duplicate id %s' %(id)



    security.declarePrivate('storeScript')
    def storeScript(self, script ):
        """ store a script"""
        self.validateId(script.get('id'), self.getScripts())
        scripts = list(self.scripts)
        if len(scripts) and scripts[0].get('id') == 'ploneCustom.css':
            scripts.insert(1, script)
        else:
            scripts.insert(0, script )
        self.scripts = tuple(scripts)
        self.cookScripts()


    security.declareProtected(permissions.ManagePortal, 'getScripts')
    def getScripts(self ):
        """ get all the registered script data, uncooked. for management screens """
        return tuple([item.copy() for item in self.scripts])

    security.declareProtected(permissions.ManagePortal, 'unregisterScript')
    def unregisterScript(self, id ):
        """ unregister a registered script """
        scripts = [ item for item in self.getScripts() if item.get('id') != id ]
        self.scripts = tuple(scripts)
        self.cookScripts()


    security.declarePrivate('clearScripts')
    def clearScripts(self):
        """ Clears all script data. Convenience funtion for Plone migrations and tests"""
        self.scripts = ()
        self.cookedscripts = ()
        self.concatenatedscripts = {}

    ##################################
    # ZMI METHODS
    #

    security.declareProtected(permissions.ManagePortal, 'manage_registerScript')
    def manage_addScript(self,id, expression='', inline=False, enabled=True, REQUEST=None):
        """ register a script from a TTW request"""
        self.registerScript(id, expression, inline, enabled)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_saveScripts')
    def manage_saveScripts(self, REQUEST=None):
        """
         save scripts from the ZMI
         updates the whole sequence. for editing and reordering
        """
        records = REQUEST.form.get('scripts')
        self.scripts = ()
        scripts = []
        for r in records:
            script = {}
            script['id']         = r.get('id')
            script['expression'] = r.get('expression', '')
            script['inline']     = r.get('inline')
            script['enabled']    = r.get('enabled')

            scripts.append(script)
        self.scripts = tuple(scripts)
        self.cookScripts()
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_registerScript')
    def manage_removeScript(self, id, REQUEST=None):
        """ remove script with ZMI button"""
        self.unregisterScript(id)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'getScripts')
    def getScripts(self):
        """ get the scripts for management screens """
        return tuple([item.copy() for item in self.scripts])

    security.declarePrivate('getScriptsDict')
    def getScriptsDict(self):
        """ get the scripts as a disctionary instead of an ordered list. Good for lookups. internal"""
        scripts = self.getScripts()
        d = {}
        for s in scripts:
            d[s['id']]=s
        return d


    def compareScripts(self, s1, s2 ):
        for attr in ('expression', 'inline'):
            if s1.get(attr) != s2.get(attr):
                return 0
        return 1

    def generateId(self):
        base = "ploneScripts"
        appendix = ".js"
        return "%s%04d%s" % (base, random.randint(0, 9999), appendix)

    def cookScripts(self ):

        scripts = self.getScripts()
        self.concatenatedscripts = {}
        self.cookedscripts = ()
        results = []
        for script in [s for s in scripts if s.get('enabled')]:
            #self.concatenatedscripts[script['id']] = [script['id']]
            if results:
                previtem = results[-1]
                if self.compareScripts(script, previtem):
                    previd = previtem.get('id')

                    if self.concatenatedscripts.has_key(previd):
                        self.concatenatedscripts[previd].append(script.get('id'))
                    else:
                        magicId = self.generateId()
                        self.concatenatedscripts[magicId] = [previd, script.get('id')]
                        previtem['id'] = magicId
                else:
                    results.append(script)
            else:
                results.append(script)
        #for entry in self.concatenatedscripts.:


        scripts = self.getScripts()
        for script in scripts:
            self.concatenatedscripts[script['id']] = [script['id']]
        self.cookedscripts = tuple(results)


    security.declareProtected(permissions.View, 'getEvaluatedScripts')
    def getEvaluatedScripts(self, context ):
        results = self.cookedscripts
        # filter results by expression
        results = [item for item in results if self.evaluateExpression(item.get('expression'), context )]
        results.reverse()
        return results

    security.declarePrivate('evaluateExpression')
    def evaluateExpression(self, expression, context):
        """
        Evaluate an object's TALES condition to see if it should be
        displayed
        """
        try:
            if expression and context is not None:
                portal = getToolByName(self, 'portal_url').getPortalObject()

                # Find folder (code courtesy of CMFCore.ActionsTool)
                if context is None or not hasattr(context, 'aq_base'):
                    folder = portal
                else:
                    folder = context
                    # Search up the containment hierarchy until we find an
                    # object that claims it's PrincipiaFolderish.
                    while folder is not None:
                        if getattr(aq_base(folder), 'isPrincipiaFolderish', 0):
                            # found it.
                            break
                        else:
                            folder = aq_parent(aq_inner(folder))

                __traceback_info__ = (folder, portal, context, expression)
                ec = createExprContext(folder, portal, context)
                return Expression(expression)(ec)
            else:
                return 1
        except AttributeError:
            return 1


    def getScript(self, item, context):
        """ fetch script for delivery"""
        ids = self.concatenatedscripts.get(item,None)
        if ids is not None:
            ids = ids[:]

        output = ""
        scripts = self.getScriptsDict()

        for id in ids:
            try:
                obj = getattr(context, id)
            except AttributeError, KeyError:
                output += "\n/* XXX ERROR -- could not find '%s' XXX */\n"%(id)
                content=""
                obj = None

            if obj is not None:
                if hasattr(aq_base(obj),'meta_type') and obj.meta_type in ['DTML Method','Filesystem DTML Method']:
                    content = obj( client=self.aq_parent, REQUEST=self.REQUEST, RESPONSE=self.REQUEST.RESPONSE)
                # we should add more explicit type-matching checks.
                elif hasattr(aq_base(obj), 'index_html') and callable(obj.index_html):
                    content = obj.index_html(self.REQUEST, self.REQUEST.RESPONSE)
                elif callable(obj):
                    content = obj(self.REQUEST, self.REQUEST.RESPONSE)
                else:
                    content = str(obj)

            # add start/end notes to the script
            # makes for better understanding and debugging
            if content:
                output += "\n/* ----- %s ----- */\n" % (id,)
                output += content
        return output

    def getInlineScript(self, item, context):
        """ return a script as inline code, not as a file object.
            Needs to take care not to mess up http headers
        """
        headers = self.REQUEST.RESPONSE.headers.copy()
        # save the RESPONSE headers
        output = self.getScript(item, context)
        # file objects and other might manipulate the headers,
        # something we don't want. we set the saved headers back.
        self.REQUEST.RESPONSE.headers = headers
        # this should probably be solved a cleaner way.
        return str(output)


    def __getitem__(self, item):
        """ Return a script from the registry """
        output = self.getScript(item, self)
        self.REQUEST.RESPONSE.setHeader('Expires',(DateTime()+(config.JS_CACHE_DURATION)).strftime('%a, %d %b %Y %H:%M:%S %Z'))
        return File(item, item, output, "application/x-javascript").__of__(self)


    def __bobo_traverse__(self, REQUEST, name):
        """ traversal hook"""
        if REQUEST is not None and self.concatenatedscripts.get(name,None) is not None:
            return self.__getitem__(name)
        obj = getattr(self, name, None)
        if obj is not None:
            return obj
        raise AttributeError('%s'%(name,))


InitializeClass(JSRegistryTool)
