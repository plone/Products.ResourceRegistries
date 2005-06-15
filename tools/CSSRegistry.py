from DateTime import DateTime
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import ICSSRegistry
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool


class CSSRegistryTool(BaseRegistryTool):
    """A Plone registry for managing the linking to css files."""

    id = config.CSSTOOLNAME
    meta_type = config.CSSTOOLTYPE
    title = 'CSS Registry'

    security = ClassSecurityInfo()

    __implements__ = (BaseRegistryTool.__implements__, ICSSRegistry,)

    #
    # ZMI stuff
    #

    manage_cssForm = PageTemplateFile('www/cssconfig', config.GLOBALS)
    manage_cssComposition = PageTemplateFile('www/csscomposition', config.GLOBALS)

    manage_options = (
        {
            'label': 'CSS Registry',
            'action': 'manage_cssForm',
        },
        {
            'label': 'Merged CSS Composition',
            'action': 'manage_cssComposition',
        },
    ) + BaseRegistryTool.manage_options

    #
    # Private Methods
    #

    def __init__(self):
        """Initialize CSS Registry."""
        BaseRegistryTool.__init__(self)
        self.attributes_to_compare = ('expression', 'inline')
        self.filename_base = 'ploneStyles'
        self.filename_appendix = '.css'
        self.merged_output_prefix = ''
        self.cache_duration = config.CSS_CACHE_DURATION

    security.declarePrivate('storeResource')
    def storeResource(self, resource):
        """Store a resource."""
        self.validateId(resource.get('id'), self.getResources())
        resources = list(self.resources)
        if len(resources) and resources[-1].get('id') == 'ploneCustom.css':
            # ploneCustom.css should be the last item
            resources.insert(-1, resource)
        else:
            resources.append(resource)
        self.resources = tuple(resources)
        self.cookResources()

    security.declarePrivate('clearStylesheets')
    def clearStylesheets(self):
        self.clearResources()

    security.declarePrivate('compareStylesheets')
    def compareStylesheets(self, sheet1, sheet2 ):
        """Check if two resources are compatible."""
        for attr in ('expression', 'rel', 'rendering'):
            if sheet1.get(attr) != sheet2.get(attr):
                return 0
            if 'alternate' in sheet1.get('rel'):
                return 0
                # this part needs a test
        return 1

    security.declarePrivate('finalizeResourceMerging')
    def finalizeResourceMerging(self, resource, previtem):
        """Finalize the resource merging with the previous item."""
        if previtem.get('media') != resource.get('media'):
            previtem['media'] = None

    security.declarePrivate('finalizeContent')
    def finalizeContent(self, resource, content):
        """Finalize the resource content."""
        m = resource.get('media')
        if m:
            return '@media %s {\n%s\n}\n' % (m, content)
        return content

    #
    # ZMI Methods
    #

    security.declareProtected(permissions.ManagePortal, 'manage_addStylesheet')
    def manage_addStylesheet(self, id, expression='', media='',
                             rel='stylesheet', title='', rendering='import',
                             enabled=True, REQUEST=None):
        """Register a stylesheet from a TTW request."""
        self.registerStylesheet(id, expression, media, rel, title,
                                rendering, enabled)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_saveStylesheets')
    def manage_saveStylesheets(self, REQUEST=None):
        """Save stylesheets from the ZMI.

        Updates the whole sequence. For editing and reordering.
        """
        debugmode = REQUEST.get('debugmode',False)
        self.setDebugMode(debugmode)
        records = REQUEST.get('stylesheets')
        records.sort(lambda a, b: a.sort - b.sort)
        self.resources = ()
        stylesheets = []
        for r in records:
            stylesheet = {}
            stylesheet['id'] = r.get('id')
            stylesheet['expression'] = r.get('expression', '')
            stylesheet['media'] = r.get('media', '')
            stylesheet['rel'] = r.get('rel', 'stylesheet')
            stylesheet['title'] = r.get('title', '')
            stylesheet['rendering'] = r.get('rendering', 'import')
            stylesheet['enabled'] = r.get('enabled', False)
            stylesheets.append(stylesheet)
        self.resources = tuple(stylesheets)
        self.cookResources()
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_removeStylesheet')
    def manage_removeStylesheet(self, id, REQUEST=None):
        """Remove stylesheet from the ZMI."""
        self.unregisterResource(id)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    #
    # Protected Methods
    #

    security.declareProtected(permissions.ManagePortal, 'registerStylesheet')
    def registerStylesheet(self, id, expression='', media='', rel='stylesheet',
                           title='', rendering='import',  enabled=1):
        """Register a stylesheet."""
        stylesheet = {}
        stylesheet['id'] = id
        stylesheet['expression'] = expression
        stylesheet['media'] = media
        stylesheet['rel'] = rel
        stylesheet['title'] = title
        stylesheet['rendering'] = rendering
        stylesheet['enabled'] = enabled
        self.storeResource(stylesheet)

    security.declareProtected(permissions.ManagePortal, 'getRenderingOptions')
    def getRenderingOptions(self):
        """Rendering methods for use in ZMI forms."""
        return config.CSS_RENDER_METHODS

    security.declareProtected(permissions.View, 'getContentType')
    def getContentType(self):
        """Return the registry content type."""
        return 'text/css'


InitializeClass(CSSRegistryTool)
