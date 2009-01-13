from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.interface import implements

from Products.CMFCore.utils import getToolByName

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import ICSSRegistry
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool
from Products.ResourceRegistries.tools.BaseRegistry import Resource

from packer import CSSPacker


class Stylesheet(Resource):
    security = ClassSecurityInfo()

    def __init__(self, id, **kwargs):
        Resource.__init__(self, id, **kwargs)
        self._data['media'] = kwargs.get('media', '')
        self._data['rel'] = kwargs.get('rel', 'stylesheet')
        self._data['title'] = kwargs.get('title', '')
        self._data['rendering'] = kwargs.get('rendering', 'import')
        self._data['compression'] = kwargs.get('compression', 'safe')

    security.declarePublic('getMedia')
    def getMedia(self):
        result = self._data['media']
        if result == "":
            result = None
        return result

    security.declareProtected(permissions.ManagePortal, 'setMedia')
    def setMedia(self, media):
        self._data['media'] = media

    security.declarePublic('getRel')
    def getRel(self):
        return self._data['rel']

    security.declareProtected(permissions.ManagePortal, 'setRel')
    def setRel(self, rel):
        self._data['rel'] = rel

    security.declarePublic('getTitle')
    def getTitle(self):
        result = self._data['title']
        if result == "":
            result = None
        return result

    security.declareProtected(permissions.ManagePortal, 'setTitle')
    def setTitle(self, title):
        self._data['title'] = title

    security.declarePublic('getRendering')
    def getRendering(self):
        return self._data['rendering']

    security.declareProtected(permissions.ManagePortal, 'setRendering')
    def setRendering(self, rendering):
        self._data['rendering'] = rendering

    security.declarePublic('getCompression')
    def getCompression(self):
        # as this is a new property, old instance might not have that value, so
        # return 'safe' as default
        compression = self._data.get('compression', 'safe')
        if compression in config.CSS_COMPRESSION_METHODS:
            return compression
        return 'none'

    security.declareProtected(permissions.ManagePortal, 'setCompression')
    def setCompression(self, compression):
        self._data['compression'] = compression

InitializeClass(Stylesheet)


class CSSRegistryTool(BaseRegistryTool):
    """A Plone registry for managing the linking to css files."""

    id = config.CSSTOOLNAME
    meta_type = config.CSSTOOLTYPE
    title = 'CSS Registry'

    security = ClassSecurityInfo()

    implements(ICSSRegistry)

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

    attributes_to_compare = ('getExpression', 'getCookable',
                             'getCacheable', 'getRel', 'getRendering',
                             'getConditionalcomment')
    filename_base = 'ploneStyles'
    filename_appendix = '.css'
    merged_output_prefix = u''
    cache_duration = config.CSS_CACHE_DURATION
    resource_class = Stylesheet

    #
    # Private Methods
    #

    security.declarePrivate('storeResource')
    def storeResource(self, resource, skipCooking=False):
        """Store a resource."""
        self.validateId(resource.getId(), self.getResources())
        resources = list(self.getResources())
        if len(resources) and resources[-1].getId() == 'ploneCustom.css':
            # ploneCustom.css should be the last item
            resources.insert(-1, resource)
        else:
            resources.append(resource)
        self.resources = tuple(resources)
        if not skipCooking:
            self.cookResources()

    security.declarePrivate('clearStylesheets')
    def clearStylesheets(self):
        self.clearResources()

    security.declarePrivate('compareResources')
    def compareResources(self, sheet1, sheet2 ):
        """Check if two resources are compatible."""
        for attr in self.attributes_to_compare:
            if getattr(sheet1, attr)() != getattr(sheet2, attr)():
                return False
            if 'alternate' in sheet1.getRel():
                return False
                # this part needs a test
        return True

    security.declarePrivate('finalizeResourceMerging')
    def finalizeResourceMerging(self, resource, previtem):
        """Finalize the resource merging with the previous item."""
        if previtem.getMedia() != resource.getMedia():
            previtem.setMedia(None)

    def _compressCSS(self, content, level='safe'):
        if level == 'full':
            return CSSPacker('full').pack(content)
        elif level == 'safe':
            return CSSPacker('safe').pack(content)
        else:
            return content

    security.declarePrivate('finalizeContent')
    def finalizeContent(self, resource, content):
        """Finalize the resource content."""
        compression = resource.getCompression()
        if compression != 'none' and not self.getDebugMode():
            orig_url = "%s/%s?original=1" % (self.absolute_url(), resource.getId())
            content = "/* %s */\n%s" % (orig_url,
                                     self._compressCSS(content, compression))

        m = resource.getMedia()
        if m:
            content = '@media %s {\n%s\n}\n' % (m, content)

        return content

    #
    # ZMI Methods
    #

    security.declareProtected(permissions.ManagePortal, 'manage_addStylesheet')
    def manage_addStylesheet(self, id, expression='', media='',
                             rel='stylesheet', title='', rendering='import',
                             enabled=False, cookable=True, compression='safe',
                             cacheable=True, REQUEST=None, conditionalcomment=''):
        """Register a stylesheet from a TTW request."""
        self.registerStylesheet(id, expression, media, rel, title,
                                rendering, enabled, cookable, compression,
                                cacheable, conditionalcomment)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_saveStylesheets')
    def manage_saveStylesheets(self, REQUEST=None):
        """Save stylesheets from the ZMI.

        Updates the whole sequence. For editing and reordering.
        """
        debugmode = REQUEST.get('debugmode',False)
        self.setDebugMode(debugmode)
        autogroupingmode = REQUEST.get('autogroupingmode', False)
        self.setAutoGroupingMode(autogroupingmode)
        records = REQUEST.get('stylesheets')
        records.sort(lambda a, b: a.sort - b.sort)
        self.resources = ()
        stylesheets = []
        for r in records:
            stylesheet = Stylesheet(r.get('id'),
                                    expression=r.get('expression', ''),
                                    media=r.get('media', ''),
                                    rel=r.get('rel', 'stylesheet'),
                                    title=r.get('title', ''),
                                    rendering=r.get('rendering', 'import'),
                                    enabled=r.get('enabled', False),
                                    cookable=r.get('cookable', False),
                                    cacheable=r.get('cacheable', False),
                                    compression=r.get('compression', 'safe'),
                                    conditionalcomment=r.get('conditionalcomment',''))
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
                           title='', rendering='import',  enabled=1,
                           cookable=True, compression='safe', cacheable=True,
                           skipCooking=False, conditionalcomment=''):
        """Register a stylesheet."""
        stylesheet = Stylesheet(id,
                                expression=expression,
                                media=media,
                                rel=rel,
                                title=title,
                                rendering=rendering,
                                enabled=enabled,
                                cookable=cookable,
                                compression=compression,
                                cacheable=cacheable,
                                conditionalcomment=conditionalcomment)
        self.storeResource(stylesheet, skipCooking=skipCooking)

    security.declareProtected(permissions.ManagePortal, 'updateStylesheet')
    def updateStylesheet(self, id, **data):
        stylesheet = self.getResourcesDict().get(id, None)
        if stylesheet is None:
            raise ValueError, 'Invalid resource id %s' % (id)
        
        if data.get('expression', None) is not None:
            stylesheet.setExpression(data['expression'])
        if data.get('media', None) is not None:
            stylesheet.setMedia(data['media'])
        if data.get('rel', None) is not None:
            stylesheet.setRel(data['rel'])
        if data.get('title', None) is not None:
            stylesheet.setTitle(data['title'])
        if data.get('rendering', None) is not None:
            stylesheet.setRendering(data['rendering'])
        if data.get('enabled', None) is not None:
            stylesheet.setEnabled(data['enabled'])
        if data.get('cookable', None) is not None:
            stylesheet.setCookable(data['cookable'])
        if data.get('compression', None) is not None:
            stylesheet.setCompression(data['compression'])
        if data.get('cacheable', None) is not None:
            stylesheet.setCacheable(data['cacheable'])
        if data.get('conditionalcomment',None) is not None:
            stylesheet.setConditionalcomment(data['conditionalcomment'])

    security.declareProtected(permissions.ManagePortal, 'getRenderingOptions')
    def getRenderingOptions(self):
        """Rendering methods for use in ZMI forms."""
        return config.CSS_RENDER_METHODS

    security.declareProtected(permissions.ManagePortal, 'getCompressionOptions')
    def getCompressionOptions(self):
        """Compression methods for use in ZMI forms."""
        return config.CSS_COMPRESSION_METHODS

    security.declareProtected(permissions.View, 'getContentType')
    def getContentType(self):
        """Return the registry content type."""
        plone_utils = getToolByName(self, 'plone_utils')
        try:
            encoding = plone_utils.getSiteEncoding()
        except AttributeError:
            # For Plone < 2.1
            pprop = getToolByName(self, 'portal_properties')
            default = 'utf-8'
            try:
                encoding = pprop.site_properties.getProperty('default_charset', default)
            except AttributeError:
                encoding = default
        return 'text/css;charset=%s' % encoding


InitializeClass(CSSRegistryTool)
