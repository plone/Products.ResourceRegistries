from zope.interface import implements

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Acquisition import aq_parent

from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import ICSSRegistry
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool
from Products.ResourceRegistries.tools.BaseRegistry import Resource

from Products.ResourceRegistries.utils import applyPrefix

from packer import CSSPacker
import logging


class Stylesheet(Resource):
    security = ClassSecurityInfo()

    def __init__(self, id, **kwargs):
        Resource.__init__(self, id, **kwargs)
        self._data['media'] = kwargs.get('media', 'screen')
        self._data['rel'] = kwargs.get('rel', 'stylesheet')
        self._data['title'] = kwargs.get('title', '')
        self._data['rendering'] = kwargs.get('rendering', 'link')
        self._data['compression'] = kwargs.get('compression', 'safe')
        self._data['applyPrefix'] = kwargs.get('applyPrefix', False)
        if self.isExternal:
            if id.startswith('//') and self._data['rendering'] != 'link':
                # force a link. it doesn't make sense any other way
                logging.warning(u'Stylesheets beginning with // must be rendered as links. Updated for you.')
                self._data['rendering'] = 'link'
            if self._data['compression'] not in config.CSS_EXTERNAL_COMPRESSION_METHODS:
                self._data['compression'] = 'none' #we have to assume none because of the default values
            if self._data['rendering'] not in config.CSS_EXTERNAL_RENDER_METHODS:
                raise ValueError("Render method %s not allowed for External Resource" % (self._data['rendering'],))

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
        if self.isExternalResource() and rendering not in config.CSS_EXTERNAL_RENDER_METHODS:
            raise ValueError("Rendering method %s not valid, must be one of: %s" % (
                             rendering, ', '.join(config.CSS_EXTERNAL_RENDER_METHODS)))
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
        if self.isExternalResource() and compression not in config.CSS_COMPRESSION_METHODS:
            raise ValueError("Compression method %s not valid, must be one of: %s" % (
                             compression, ', '.join(config.CSS_EXTERNAL_COMPRESSION_METHODS)))
        self._data['compression'] = compression

    security.declareProtected(permissions.ManagePortal, 'setApplyPrefix')
    def setApplyPrefix(self, applyPrefix):
        self._data['applyPrefix'] = applyPrefix

    security.declarePublic('getApplyPrefix')
    def getApplyPrefix(self):
        return self._data.get('applyPrefix', False)

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

    attributes_to_compare = ('getAuthenticated', 'getExpression',
                             'getCookable', 'getCacheable', 'getRel',
                             'getRendering', 'getConditionalcomment')
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
        self.validateId(resource.getId(), self.resources)
        resources = list(self.resources)
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
        if 'alternate' in sheet1.getRel():
            return False
            # this part needs a test
        if sheet1.isExternalResource():
            return False
        for attr in self.attributes_to_compare:
            if getattr(sheet1, attr)() != getattr(sheet2, attr)():
                return False

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
        
        if resource.getApplyPrefix() and not self.getDebugMode():
            prefix = aq_parent(self).absolute_url_path()
            if prefix.endswith('/'):
                prefix = prefix[:-1]
            
            resourceName = resource.getId()
            
            if '/' in resourceName:
                prefix += '/' + '/'.join(resourceName.split('/')[:-1])
            
            content = applyPrefix(content, prefix)
        
        return content

    #
    # ZMI Methods
    #

    security.declareProtected(permissions.ManagePortal, 'manage_addStylesheet')
    def manage_addStylesheet(self, id, expression='', media='screen',
                             rel='stylesheet', title='', rendering='link',
                             enabled=False, cookable=True, compression='safe',
                             cacheable=True, REQUEST=None,
                             conditionalcomment='', authenticated=False,
                             applyPrefix=False, bundle='default'):
        """Register a stylesheet from a TTW request."""
        self.registerStylesheet(id, expression, media, rel, title,
                                rendering, enabled, cookable, compression,
                                cacheable, conditionalcomment, authenticated,
                                applyPrefix=applyPrefix, bundle=bundle)
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    security.declareProtected(permissions.ManagePortal, 'manage_saveStylesheets')
    def manage_saveStylesheets(self, REQUEST=None):
        """Save stylesheets from the ZMI.

        Updates the whole sequence. For editing and reordering.
        """
        if REQUEST and not REQUEST.form:
            REQUEST.RESPONSE.redirect("manage_workspace")
            return
        debugmode = REQUEST.get('debugmode', False)
        self.setDebugMode(debugmode)
        records = REQUEST.get('stylesheets', [])
        records.sort(lambda a, b: a.sort - b.sort)
        self.resources = ()
        stylesheets = []
        for r in records:
            stylesheet = self.resource_class(
                                    r.get('id'),
                                    expression=r.get('expression', ''),
                                    media=r.get('media', 'screen'),
                                    rel=r.get('rel', 'stylesheet'),
                                    title=r.get('title', ''),
                                    rendering=r.get('rendering', 'link'),
                                    enabled=r.get('enabled', True),
                                    cookable=r.get('cookable', False),
                                    cacheable=r.get('cacheable', True),
                                    compression=r.get('compression', 'safe'),
                                    conditionalcomment=r.get('conditionalcomment',''),
                                    authenticated=r.get('authenticated', False),
                                    applyPrefix=r.get('applyPrefix', False),
                                    bundle=r.get('bundle', 'default'))
            stylesheets.append(stylesheet)
        self.resources = tuple(stylesheets)
        self.cookResources()
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    security.declareProtected(permissions.ManagePortal, 'manage_removeStylesheet')
    def manage_removeStylesheet(self, id, REQUEST=None):
        """Remove stylesheet from the ZMI."""
        self.unregisterResource(id)
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    #
    # Protected Methods
    #

    security.declareProtected(permissions.ManagePortal, 'registerStylesheet')
    def registerStylesheet(self, id, expression='', media='screen',
                           rel='stylesheet', title='', rendering='link',
                           enabled=1, cookable=True, compression='safe',
                           cacheable=True, conditionalcomment='',
                           authenticated=False, skipCooking=False,
                           applyPrefix=False, bundle='default'):
        """Register a stylesheet."""
        
        if not id:
            raise ValueError("id is required")
        
        stylesheet = self.resource_class(
                                id,
                                expression=expression,
                                media=media,
                                rel=rel,
                                title=title,
                                rendering=rendering,
                                enabled=enabled,
                                cookable=cookable,
                                compression=compression,
                                cacheable=cacheable,
                                conditionalcomment=conditionalcomment,
                                authenticated=authenticated,
                                applyPrefix=applyPrefix,
                                bundle=bundle)
        self.storeResource(stylesheet, skipCooking=skipCooking)

    security.declareProtected(permissions.ManagePortal, 'updateStylesheet')
    def updateStylesheet(self, id, **data):
        stylesheet = self.getResourcesDict().get(id, None)
        if stylesheet is None:
            raise ValueError('Invalid resource id %s' % (id))
        
        if data.get('expression', None) is not None:
            stylesheet.setExpression(data['expression'])
        if data.get('authenticated', None) is not None:
            stylesheet.setAuthenticated(data['authenticated'])
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
        if data.get('applyPrefix',None) is not None:
            stylesheet.setApplyPrefix(data['applyPrefix'])
        if data.get('bundle', None) is not None:
            stylesheet.setBundle(data['bundle'])

    security.declareProtected(permissions.ManagePortal, 'getRenderingOptions')
    def getRenderingOptions(self):
        """Rendering methods for use in ZMI forms."""
        return config.CSS_RENDER_METHODS

    security.declareProtected(permissions.ManagePortal, 'getCompressionOptions')
    def getCompressionOptions(self):
        """Compression methods for use in ZMI forms."""
        return config.CSS_COMPRESSION_METHODS
    
    security.declareProtected(permissions.ManagePortal, 'getExternalRenderingOptions')
    def getExternalRenderingOptions(self):
        """Rendering methods for use in ZMI forms."""
        return config.CSS_EXTERNAL_RENDER_METHODS

    security.declareProtected(permissions.ManagePortal, 'getExternalCompressionOptions')
    def getExternalCompressionOptions(self):
        """Compression methods for use in ZMI forms."""
        return config.CSS_EXTERNAL_COMPRESSION_METHODS

    security.declareProtected(permissions.View, 'getContentType')
    def getContentType(self):
        """Return the registry content type."""
        return 'text/css;charset=utf-8'


InitializeClass(CSSRegistryTool)
