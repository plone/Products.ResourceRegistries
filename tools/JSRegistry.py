from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from Acquisition import aq_base, aq_parent 

from Products.CSSRegistry import config
from Products.CSSRegistry import permissions
from Products.CSSRegistry.interfaces import IJSRegistry

from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext

from OFS.Image import File

import random


class JSRegistryTool(UniqueObject, SimpleItem, PropertyManager):
    """An example tool.
    """

    id = config.JSTOOLNAME
    meta_type = config.JSTOOLTYPE

    security = ClassSecurityInfo()

    __implements__ = (SimpleItem.__implements__, IJSRegistry,)

    def __init__(self ):
        """ add the storages """
        self.scripts = ()
        self.cookedscripts = ()
        self.concatenatedscripts = {}


    security.declareProtected(permissions.ManagePortal, 'registerScript')
    def registerScript(self, id, expression='', contenttype='text/javascript', inline=0, enabled=1):
        """ register a script"""
        script = {}
        script['id'] = id
        script['expression'] = expression 
        script['contenttype'] = media
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

    
    security.declareProtected(permissions.ManagePortal, 'getStylesheets')
    def getScripts(self ):
        """ sdf """
        
        raise NotImplemented
        #return tuple([item.copy() for item in self.scripts])
        
    security.declareProtected(permissions.ManagePortal, 'unregisterStylesheet')        
    def unregisterScript(self, id ):
        """ unreginster a registered script """
        
        raise NotImplemented
        #scripts = [ item for item in self.getStylesheets() if item.get('id') != id ]
        #self.scripts = tuple(scripts)
        #self.cookStylesheets()
        
    
    
    def compareScripts(self, sheet1, sheet2 ):
        
        raise NotImplemented
        #for attr in ('expression', 'media', 'rel', 'cssimport', 'inline'):
        #    if sheet1.get(attr) != sheet2.get(attr):
        #        return 0
        #return 1
                            
    def generateId(self):
        base = "ploneJavascripts"
        appendix = ".js"
        return "%s%04d%s" % (base, random.randint(0, 9999), appendix)
                            
    def cookScripts(self ):
        raise NotImplemented
        #scripts = self.getStylesheets()
        #self.concatenatedscripts = {}
        #self.cookedscripts = ()
        #results = []
        #for script in scripts:
        #    #self.concatenatedscripts[script['id']] = [script['id']]
        #    if results:
        #        previtem = results[-1]
        #        if self.compareStylesheets(script, previtem):
        #            previd = previtem.get('id')
        #
        #            if self.concatenatedscripts.has_key(previd):
        #                self.concatenatedscripts[previd].append(script.get('id'))
        #            else:
        #                magicId = self.generateId()
        #                self.concatenatedscripts[magicId] = [previd, script.get('id')]
        #                previtem['id'] = magicId
        #        else:
        #            results.append(script)    
        #    else:
        #        results.append(script)
        ##for entry in self.concatenatedscripts.:
        #    
        #    
        #scripts = self.getStylesheets()
        #for script in scripts:
        #    self.concatenatedscripts[script['id']] = [script['id']]
        #self.cookedscripts = tuple(results)
        
        
    security.declareProtected(permissions.View, 'getEvaluatedScripts')        
    def getEvaluatedScripts(self, context ):
        raise NotImplemented
        #results = self.cookedscripts
        ## filter results by expression
        #results = [item for item in results if self.evaluateExpression(item.get('expression'), context )]    
        #results.reverse()
        #return results
         
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
        
    
    def __getitem__(self, item):
        """ Return a script from the registry """
        ids = self.concatenatedscripts[item]
        output = ""
        for id in ids:
            obj = getattr(self.aq_parent, id)
            if hasattr(aq_base(obj), 'index_html') and callable(obj.index_html):
                content = obj.index_html(self.REQUEST, self.REQUEST.RESPONSE)
            else:
                content = str(obj)
            
            output += content # This needs to be fixed to render the object first
            
        return File(item, item, output, "text/javascript").__of__(self)
        
InitializeClass(JSRegistryTool)
