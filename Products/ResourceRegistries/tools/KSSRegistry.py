from zope.interface import implements

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import IKSSRegistry
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool
from Products.ResourceRegistries.tools.BaseRegistry import Resource

from packer import CSSPacker


class KineticStylesheet(Resource):
    security = ClassSecurityInfo()

    def __init__(self, id, **kwargs):
        Resource.__init__(self, id, **kwargs)
        self._data['compression'] = kwargs.get('compression', 'safe')
        if self.isExternal:
            self._data['compression'] = 'none' #External resources are not compressable

    security.declarePublic('getCompression')
    def getCompression(self):
        # as this is a new property, old instance might not have that value, so
        # return 'safe' as default
        compression = self._data.get('compression', 'safe')
        if compression in config.KSS_COMPRESSION_METHODS:
            return compression
        return 'none'

    security.declareProtected(permissions.ManagePortal, 'setCompression')
    def setCompression(self, compression):
        if self.isExternalResource() and compression not in config.KSS_EXTERNAL_COMPRESSION_METHODS:
            raise ValueError("Compression method %s must be one of: %s for External Resources" % (
                             compression, ', '.join(config.KSS_EXTERNAL_COMPRESSION_METHODS)))
        self._data['compression'] = compression

InitializeClass(KineticStylesheet)


class KSSRegistryTool(BaseRegistryTool):
    """A Plone registry for managing the linking to kss files."""

    id = config.KSSTOOLNAME
    meta_type = config.KSSTOOLTYPE
    title = 'KSS Registry'

    security = ClassSecurityInfo()

    implements(IKSSRegistry)

    #
    # ZMI stuff
    #

    manage_kssForm = PageTemplateFile('www/kssconfig', config.GLOBALS)
    manage_kssComposition = PageTemplateFile('www/ksscomposition', config.GLOBALS)

    manage_options = (
        {
            'label': 'KSS Registry',
            'action': 'manage_kssForm',
        },
        {
            'label': 'Merged KSS Composition',
            'action': 'manage_kssComposition',
        },
    ) + BaseRegistryTool.manage_options

    attributes_to_compare = ('getAuthenticated', 'getExpression',
                             'getCookable', 'getCacheable',
                             'getConditionalcomment')
    filename_base = 'ploneStyles'
    filename_appendix = '.kss'
    merged_output_prefix = u''
    cache_duration = config.KSS_CACHE_DURATION
    resource_class = KineticStylesheet

    @property
    def manage_workspace_url(self):
        return "%s/manage_workspace" % self.absolute_url_path()

    #
    # Private Methods
    #

    security.declarePrivate('clearKineticStylesheets')
    def clearKineticStylesheets(self):
        self.clearResources()

    def _compressKSS(self, content, level='safe'):
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
                                     self._compressKSS(content, compression))

        return content

    #
    # ZMI Methods
    #

    security.declareProtected(permissions.ManagePortal, 'manage_addKineticStylesheet')
    def manage_addKineticStylesheet(self, id, expression='', media='screen',
                             rel='stylesheet', title='', rendering='import',
                             enabled=False, cookable=True, compression='safe',
                             cacheable=True, conditionalcomment='', authenticated=False,
                             bundle='default', REQUEST=None):
        """Register a kineticstylesheet from a TTW request."""
        self.registerKineticStylesheet(id, expression, enabled,
                                       cookable, compression, cacheable,
                                       conditionalcomment, authenticated, bundle=bundle)
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    security.declareProtected(permissions.ManagePortal, 'manage_saveKineticStylesheets')
    def manage_saveKineticStylesheets(self, REQUEST=None):
        """Save kineticstylesheets from the ZMI.

        Updates the whole sequence. For editing and reordering.
        """
        if REQUEST and not REQUEST.form:
            REQUEST.RESPONSE.redirect("manage_workspace")
            return
        debugmode = REQUEST.get('debugmode', False)
        self.setDebugMode(debugmode)
        records = REQUEST.get('kineticstylesheets', [])
        records.sort(lambda a, b: a.sort - b.sort)
        self.resources = ()
        kineticstylesheets = []
        for r in records:
            kss = self.resource_class(
                                    r.get('id'),
                                    expression=r.get('expression', ''),
                                    enabled=r.get('enabled', True),
                                    cookable=r.get('cookable', True),
                                    cacheable=r.get('cacheable', True),
                                    compression=r.get('compression', 'safe'),
                                    conditionalcomment=r.get('conditionalcomment',''),
                                    authenticated=r.get('authenticated', False),
                                    bundle=r.get('bundle', 'default'))
            kineticstylesheets.append(kss)
        self.resources = tuple(kineticstylesheets)
        self.cookResources()
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    security.declareProtected(permissions.ManagePortal, 'manage_removeKineticStylesheet')
    def manage_removeKineticStylesheet(self, id, REQUEST=None):
        """Remove kineticstylesheet from the ZMI."""
        self.unregisterResource(id)
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    #
    # Protected Methods
    #

    security.declareProtected(permissions.ManagePortal, 'registerKineticStylesheet')
    def registerKineticStylesheet(self, id, expression='', enabled=1,
                                  cookable=True, compression='safe',
                                  cacheable=True, conditionalcomment='',
                                  authenticated=False,
                                  skipCooking=False, bundle='default'):
        """Register a kineticstylesheet."""
        kineticstylesheet = self.resource_class(id,
                                expression=expression,
                                enabled=enabled,
                                cookable=cookable,
                                compression=compression,
                                cacheable=cacheable,
                                conditionalcomment=conditionalcomment,
                                authenticated=authenticated,
                                bundle=bundle)
        self.storeResource(kineticstylesheet, skipCooking=skipCooking)

    security.declareProtected(permissions.ManagePortal, 'updateKineticStylesheet')
    def updateKineticStylesheet(self, id, **data):
        kineticstylesheet = self.getResourcesDict().get(id, None)
        if kineticstylesheet is None:
            raise ValueError('Invalid resource id %s' % (id))
        
        if data.get('expression', None) is not None:
            kineticstylesheet.setExpression(data['expression'])
        if data.get('authenticated', None) is not None:
            kineticstylesheet.setAuthenticated(data['authenticated'])
        if data.get('enabled', None) is not None:
            kineticstylesheet.setEnabled(data['enabled'])
        if data.get('cookable', None) is not None:
            kineticstylesheet.setCookable(data['cookable'])
        if data.get('compression', None) is not None:
            kineticstylesheet.setCompression(data['compression'])
        if data.get('cacheable', None) is not None:
            kineticstylesheet.setCacheable(data['cacheable'])
        if data.get('conditionalcomment', None) is not None:
            kineticstylesheet.setConditionalcomment(data['conditionalcomment'])
        if data.get('bundle', None) is not None:
            kineticstylesheet.setBundle(data['bundle'])

    security.declareProtected(permissions.ManagePortal, 'getCompressionOptions')
    def getCompressionOptions(self):
        """Compression methods for use in ZMI forms."""
        return config.KSS_COMPRESSION_METHODS
    
    security.declareProtected(permissions.ManagePortal, 'getExternalCompressionOptions')
    def getExternalCompressionOptions(self):
        """Compression methods for use in ZMI forms."""
        return config.KSS_EXTERNAL_COMPRESSION_METHODS
    
    security.declareProtected(permissions.View, 'getContentType')
    def getContentType(self):
        """Return the registry content type."""
        return 'text/css;charset=utf-8'


InitializeClass(KSSRegistryTool)
