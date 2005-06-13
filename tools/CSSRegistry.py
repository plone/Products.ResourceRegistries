from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries.interfaces import ICSSRegistry

from BaseRegistry import BaseRegistryTool
from DateTime import DateTime

class CSSRegistryTool(BaseRegistryTool):
    """ A Plone registry for managing the linking to css files.
    """

    id = config.CSSTOOLNAME
    meta_type = config.CSSTOOLTYPE
    title = "CSS Registry"

    security = ClassSecurityInfo()

    __implements__ = (BaseRegistryTool.__implements__, ICSSRegistry,)

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
         ) + BaseRegistryTool.manage_options
        )


    def __init__(self):
        """ add the storages """
        BaseRegistryTool.__init__(self)
        self.attributes_to_compare = ('expression', 'inline')
        self.filename_base = "ploneStyles"
        self.filename_appendix = ".css"
        self.merged_output_prefix = ""
        self.cache_duration = config.CSS_CACHE_DURATION


    security.declareProtected(permissions.ManagePortal, 'registerStylesheet')
    def registerStylesheet(self, id, expression='', media='', rel='stylesheet', title='', rendering='import',  enabled=1):
        """ register a stylesheet"""
        stylesheet = {}
        stylesheet['id'] = id
        stylesheet['expression'] = expression
        stylesheet['media'] = media
        stylesheet['rel'] = rel
        stylesheet['title'] = title
        stylesheet['rendering'] = rendering
        stylesheet['enabled'] = enabled
        self.storeResource(stylesheet)


    security.declarePrivate('storeResource')
    def storeResource(self, resource):
        """ store a resource"""
        self.validateId(resource.get('id'), self.getResources())
        resources = list(self.resources)
        if len(resources) and resources[-1].get('id') == 'ploneCustom.css':
            # ploneCustom.css should be the last item
            resources.insert(-1, resource)
        else:
            resources.append(resource)
        self.resources = tuple(resources)
        self.cookResources()


    ###############
    # ZMI METHODS

    security.declareProtected(permissions.ManagePortal, 'manage_addStylesheet')
    def manage_addStylesheet(self, id, expression='', media='', rel='stylesheet', title='', rendering='import', enabled=True, REQUEST=None):
        """ register a stylesheet from a TTW request"""
        self.registerStylesheet(id, expression, media, rel, title, rendering, enabled)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(permissions.ManagePortal, 'manage_saveStylesheets')
    def manage_saveStylesheets(self, REQUEST=None):
        """
         save stylesheets from the ZMI
         updates the whole sequence. for editing and reordering
        """
        debugmode = REQUEST.get('debugmode',False)
        self.setDebugMode(debugmode)
 
        records = REQUEST.get('stylesheets')
        records.sort(lambda a, b: a.sort-b.sort)
        self.resources = ()
        stylesheets = []
        for r in records:
            stylesheet = {}
            stylesheet['id']         = r.get('id')
            stylesheet['expression'] = r.get('expression', '')
            stylesheet['media']      = r.get('media', '')
            stylesheet['rel']        = r.get('rel', 'stylesheet')
            stylesheet['title']      = r.get('title', '')
            stylesheet['rendering']  = r.get('rendering','import')
            stylesheet['enabled']    = r.get('enabled', False)

            stylesheets.append(stylesheet)
        self.resources = tuple(stylesheets)
        self.cookResources()
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(permissions.ManagePortal, 'manage_removeStylesheet')
    def manage_removeStylesheet(self, id, REQUEST=None):
        """ remove stylesheet from the ZMI"""
        self.unregisterResource(id)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(permissions.ManagePortal, 'getRenderingOptions')
    def getRenderingOptions(self):
        """rendering methods for use in ZMI forms"""
        return config.CSS_RENDER_METHODS


    security.declarePrivate('compareStylesheets')
    def compareStylesheets(self, sheet1, sheet2 ):
        for attr in ('expression', 'rel', 'rendering'):
            if sheet1.get(attr) != sheet2.get(attr):
                return 0
            if 'alternate' in sheet1.get('rel'):
                return 0
                # this part needs a test
        return 1


    def finalizeResourceMerging(self, resource, previtem):
        if previtem.get('media') != resource.get('media'):
            previtem['media'] = None


    def finalizeContent(self, resource, content):
        # might be overwritten in subclasses
        m = resource.get('media')
        if m:
            return "@media %s {\n%s\n}\n" % (m, content)
        return content


    def getContentType(self):
        # should be overwritten by subclass
        return "text/css"


InitializeClass(CSSRegistryTool)