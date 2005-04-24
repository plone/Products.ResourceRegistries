from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Acquisition import aq_base, aq_parent, aq_inner

from Products.CSSRegistry import config
from Products.CSSRegistry import permissions
from Products.CSSRegistry.interfaces import ICSSRegistry

from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext

from OFS.Image import File

import random


class CSSRegistryTool(UniqueObject, SimpleItem, PropertyManager):
    """ A Plone registry for managing the linking to css files.
    """

    id = config.TOOLNAME
    meta_type = config.TOOLTYPE
    title = "CSS Registry"


    security = ClassSecurityInfo()

    __implements__ = (SimpleItem.__implements__, ICSSRegistry,)
    
    # ZMI stuff
    manage_cssForm = PageTemplateFile('www/cssconfig', config.GLOBALS)
    manage_cssComposition = PageTemplateFile('www/csscomposition', config.GLOBALS)

    
    manage_options=(
        ({ 'label'  : 'CSS Registry',
           'action' : 'manage_cssForm',
           },
          { 'label'  : 'Merged CSS Composition',
           'action' : 'manage_cssComposition',
           } 
         ) + SimpleItem.manage_options
        )    
        

    def __init__(self ):
        """ add the storages """
        self.stylesheets = ()
        self.cookedstylesheets = ()
        self.concatenatedstylesheets = {}


    security.declareProtected(permissions.ManagePortal, 'registerStylesheet')
    def registerStylesheet(self, id, expression='', media='', rel='stylesheet', rendering='import',  enabled=1 ):
        """ register a stylesheet"""
        stylesheet = {}
        stylesheet['id'] = id
        stylesheet['expression'] = expression 
        stylesheet['media'] = media
        stylesheet['rel'] = rel 
        stylesheet['rendering'] = rendering
        stylesheet['enabled'] = enabled
        self.storeStylesheet(stylesheet )


    security.declareProtected(permissions.ManagePortal, 'unregisterStylesheet')        
    def unregisterStylesheet(self, sheetid):
        """unregister a registered stylesheet"""
        stylesheets = [ item for item in self.getStylesheets() if item.get('id') != sheetid ]
        self.stylesheets = tuple(stylesheets)
        self.cookStylesheets()


    security.declarePrivate('clearStylesheets')
    def clearStylesheets(self):
        """ Clears all stylesheet data. convenience for Plone migrations"""
        self.stylesheets = ()
        self.cookedstylesheets = ()
        self.concatenatedstylesheets = {}    
    
    ###############
    # ZMI METHODS

    security.declareProtected(permissions.ManagePortal, 'manage_registerStylesheet')
    def manage_addStylesheet(self, id, expression='', media='', rel='stylesheet', rendering='import', enabled=True, REQUEST=None):
        """ register a stylesheet from a TTW request"""
        self.registerStylesheet(id, expression, media, rel, rendering, enabled)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_saveStylesheets')
    def manage_saveStylesheets(self, REQUEST=None):
        """
         save stylesheets from the ZMI 
         updates the whole sequence. for editing and reordering
        """
        records = REQUEST.get('stylesheets')
        records.sort()
        self.stylesheets = ()
        stylesheets = []
        for r in records:
            stylesheet = {}
            stylesheet['id']         = r.get('id')
            stylesheet['expression'] = r.get('expression', '') 
            stylesheet['media']      = r.get('media', '')
            stylesheet['rel']        = r.get('rel', 'stylesheet') 
            stylesheet['rendering']  = r.get('rendering','import')
            stylesheet['enabled']    = r.get('enabled', True)

            stylesheets.append(stylesheet)
        self.stylesheets = tuple(stylesheets)
        self.cookStylesheets()
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_registerStylesheet')
    def manage_removeStylesheet(self, id, REQUEST=None):
        """ remove stylesheet from the ZMI"""
        self.unregisterStylesheet(id)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'getStylesheets')
    def getStylesheets(self):
        """ get the stylesheets for management screens """
        return tuple([item.copy() for item in self.stylesheets])

    security.declarePrivate('getStylesheetsDict')
    def getStylesheetsDict(self):
        """ get the stylesheets as a disctionary insterad of an ordered list. Good for lookups. internal"""
        stylesheets = self.getStylesheets()
        d = {}
        for s in stylesheets:
            d[s['id']]=s
        return d

    security.declareProtected(permissions.ManagePortal, 'getRenderingOptions')
    def getRenderingOptions(self):
        """rendering methods for use in ZMI forms"""
        return config.CSS_RENDER_METHODS

    security.declarePrivate('validateId')
    def validateId(self, id, existing):
        """ safeguard against dulicate ids"""
        for sheet in existing:
            if sheet.get('id') == id: 
                raise ValueError, 'Duplicate id %s' %(id)            

        
    security.declarePrivate('storeStylesheet')            
    def storeStylesheet(self, stylesheet ):
        """ tupleize and store a list of styesheets"""        
        self.validateId(stylesheet.get('id'), self.getStylesheets())
        stylesheets = list(self.stylesheets)
        if len(stylesheets) and stylesheets[0].get('id') == 'ploneCustom.css':
            stylesheets.insert(1, stylesheet)
        else:
            stylesheets.insert(0, stylesheet )
        
        self.stylesheets = tuple(stylesheets)
        self.cookStylesheets()

        
    security.declarePrivate('compareStylesheets')            
    def compareStylesheets(self, sheet1, sheet2 ):
        for attr in ('expression', 'rel', 'rendering'):
            if sheet1.get(attr) != sheet2.get(attr):
                return 0
            if 'alternate' in sheet1.get('rel'):
                return 0
                # this part needs a test
        return 1

    security.declarePrivate('generateId')            
    def generateId(self):
        base = "ploneStyles"
        appendix = ".css"
        return "%s%04d%s" % (base, random.randint(0, 9999), appendix)
                                       
    security.declarePrivate('cookStylesheets')            
    def cookStylesheets(self ):
        stylesheets = self.getStylesheets()
        self.concatenatedstylesheets = {}
        self.cookedstylesheets = ()
        results = []
        for stylesheet in stylesheets:
            #self.concatenatedstylesheets[stylesheet['id']] = [stylesheet['id']]
            if results:
                previtem = results[-1]
                if self.compareStylesheets(stylesheet, previtem):
                    # the two sheets match , and should be concatenated
                    previd = previtem.get('id')
        
                    if self.concatenatedstylesheets.has_key(previd):
                        self.concatenatedstylesheets[previd].append(stylesheet.get('id'))
                    else:
                        magicId = self.generateId()
                        self.concatenatedstylesheets[magicId] = [previd, stylesheet.get('id')]
                        previtem['id'] = magicId
                else:
                    results.append(stylesheet)    
            else:
                results.append(stylesheet)
        #for entry in self.concatenatedstylesheets.:
            
            
        stylesheets = self.getStylesheets()
        for stylesheet in stylesheets:
            self.concatenatedstylesheets[stylesheet['id']] = [stylesheet['id']]
        self.cookedstylesheets = tuple(results)
        
        
    security.declareProtected(permissions.View, 'getEvaluatedStyleheets')        
    def getEvaluatedStylesheets(self, context ):
        """ get all the stylesheet references we are going to need for making proper templates"""
        results = self.cookedstylesheets    
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
        
    
    def __getitem__(self, item):
        """ Return a stylesheet from the registry """
        ids = self.concatenatedstylesheets[item][:]
        ids.reverse()
        output = ""
        
        sheets = self.getStylesheetsDict()
        
        for id in ids:
            try:
                obj = getattr(self.aq_parent, id)
            except AttributeError:
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
            
            # add start/end notes to the stylesheet
            # makes for better understanding and debugging
            if content is not None:
                output += "/* ----- start %s ----- */\n" % (id,)
                m = sheets[id].get('media')
                if not m:
                    output += content
                else:
                    output += "@media %s {\n%s\n}\n"%(m, content)

                output += "/* ----- end %s ----- */\n" % (id,)
        
        return File(item, item, output, "text/css").__of__(self)

    def __bobo_traverse__(self, REQUEST, name):
        """ traversal hook"""
        if REQUEST is not None and self.concatenatedstylesheets.get(name,None) is not None:
            return self.__getitem__(name)
        obj = getattr(self, name, None)
        if obj is not None:
            return obj
        raise AttributeError('%s'%(name,))
        


        
InitializeClass(CSSRegistryTool)    