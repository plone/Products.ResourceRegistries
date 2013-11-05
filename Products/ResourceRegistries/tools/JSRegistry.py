import re
from zope.interface import implements

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import IJSRegistry
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool
from Products.ResourceRegistries.tools.BaseRegistry import Resource

from packer import JavascriptPacker, JavascriptKeywordMapper


class JavaScript(Resource):
    security = ClassSecurityInfo()

    def __init__(self, id, **kwargs):
        Resource.__init__(self, id, **kwargs)
        self._data['inline'] = kwargs.get('inline', False)
        self._data['compression'] = kwargs.get('compression', 'safe')
        if self.isExternal:
            self._data['inline'] = False #No inline rendering for External Resources
            self._data['compression'] = 'none' #External Resources are not compressible

    security.declarePublic('getInline')
    def getInline(self):
        return self._data['inline']

    security.declareProtected(permissions.ManagePortal, 'setInline')
    def setInline(self, inline):
        if self.isExternalResource() and inline:
            raise ValueError("Inline rendering is not supported for External Resources")
        self._data['inline'] = inline

    security.declarePublic('getCompression')
    def getCompression(self):
        # as this is a new property, old instance might not have that value, so
        # return 'safe' as default
        compression = self._data.get('compression', 'safe')
        if compression in config.JS_COMPRESSION_METHODS:
            return compression
        return 'none'

    security.declareProtected(permissions.ManagePortal, 'setCompression')
    def setCompression(self, compression):
        if self.isExternalResource() and compression not in config.JS_EXTERNAL_COMPRESSION_METHODS:
            raise ValueError("Compression method '%s' must be one of: %s" % (
                             compression, ', '.join(config.JS_EXTERNAL_COMPRESSION_METHODS)))
        self._data['compression'] = compression

InitializeClass(JavaScript)


class JSRegistryTool(BaseRegistryTool):
    """A Plone registry for managing the linking to Javascript files."""

    id = config.JSTOOLNAME
    meta_type = config.JSTOOLTYPE
    title = 'JavaScript Registry'

    security = ClassSecurityInfo()

    implements(IJSRegistry)

    #
    # ZMI stuff
    #

    manage_jsForm = PageTemplateFile('www/jsconfig', config.GLOBALS)
    manage_jsComposition = PageTemplateFile('www/jscomposition', config.GLOBALS)

    manage_options = (
        {
            'label': 'Javascript Registry',
            'action': 'manage_jsForm',
        },
        {
            'label': 'Merged JS Composition',
            'action': 'manage_jsComposition',
        },
    ) + BaseRegistryTool.manage_options

    attributes_to_compare = ('getAuthenticated', 'getExpression',
                             'getCookable', 'getCacheable',
                             'getInline', 'getConditionalcomment')
    filename_base = 'ploneScripts'
    filename_appendix = '.js'
    cache_duration = config.JS_CACHE_DURATION
    merged_output_prefix = u"""
/* Merged Plone Javascript file
 * This file is dynamically assembled from separate parts.
 * Some of these parts have 3rd party licenses or copyright information attached
 * Such information is valid for that section,
 * not for the entire composite file
 * originating files are separated by - filename.js -
 */
"""
    resource_class = JavaScript

    @property
    def manage_workspace_url(self):
        return "%s/manage_workspace" % self.absolute_url_path()

    #
    # Private Methods
    #

    security.declarePrivate('clearScripts')
    def clearScripts(self):
        self.clearResources()

    def _compressJS(self, content, level='safe'):
        encode_marker = "/* sTART eNCODE */\n%s\n/* eND eNCODE */"
        if level == 'full-encode':
            return encode_marker % JavascriptPacker('full').pack(content)
        elif level == 'safe-encode':
            return encode_marker % JavascriptPacker('safe').pack(content)
        elif level == 'full':
            return JavascriptPacker('full').pack(content)
        elif level == 'safe':
            return JavascriptPacker('safe').pack(content)
        else:
            return content

    security.declarePrivate('finalizeContent')
    def finalizeContent(self, resource, content):
        """Finalize the resource content."""
        compression = resource.getCompression()
        if compression != 'none' and not self.getDebugMode():
            orig_url = "%s/%s?original=1" % (self.absolute_url(), resource.getId())
            content = "// %s\n%s" % (orig_url,
                                     self._compressJS(content, compression))

        return content

    #
    # ZMI Methods
    #

    security.declareProtected(permissions.ManagePortal, 'manage_addScript')
    def manage_addScript(self, id, expression='', inline=False,
                         enabled=False, cookable=True, compression='safe',
                         cacheable=True, conditionalcomment='',
                         authenticated=False, bundle='default', REQUEST=None):
        """Register a script from a TTW request."""
        self.registerScript(id, expression, inline, enabled, cookable,
            compression, cacheable, conditionalcomment, authenticated, bundle=bundle)
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    security.declareProtected(permissions.ManagePortal, 'manage_saveScripts')
    def manage_saveScripts(self, REQUEST=None):
        """Save scripts from the ZMI.

        Updates the whole sequence. For editing and reordering.
        """
        if REQUEST and not REQUEST.form:
            REQUEST.RESPONSE.redirect("manage_workspace")
            return
        debugmode = REQUEST.get('debugmode', False)
        self.setDebugMode(debugmode)
        records = REQUEST.form.get('scripts', [])
        records.sort(lambda a, b: a.sort-b.sort)
        self.resources = ()
        scripts = []
        for r in records:
            script = self.resource_class(
                                r.get('id'),
                                expression=r.get('expression', ''),
                                inline=r.get('inline', False),
                                enabled=r.get('enabled', True),
                                cookable=r.get('cookable', False),
                                cacheable=r.get('cacheable', True),
                                compression=r.get('compression', 'safe'),
                                conditionalcomment=r.get('conditionalcomment',''),
                                authenticated=r.get('authenticated', False),
                                bundle=r.get('bundle', 'default'))
            scripts.append(script)
        self.resources = tuple(scripts)
        self.cookResources()
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    security.declareProtected(permissions.ManagePortal, 'manage_removeScript')
    def manage_removeScript(self, id, REQUEST=None):
        """Remove script with ZMI button."""
        self.unregisterResource(id)
        if REQUEST:
            REQUEST.RESPONSE.redirect("manage_workspace")

    #
    # Protected Methods
    #

    security.declareProtected(permissions.ManagePortal, 'registerScript')
    def registerScript(self, id, expression='', inline=False, enabled=True,
                       cookable=True, compression='safe', cacheable=True,
                       conditionalcomment='', authenticated=False,
                       skipCooking=False, bundle='default'):
        """Register a script."""
        script = self.resource_class(
                            id,
                            expression=expression,
                            inline=inline,
                            enabled=enabled,
                            cookable=cookable,
                            compression=compression,
                            cacheable=cacheable,
                            conditionalcomment=conditionalcomment,
                            authenticated=authenticated,
                            bundle=bundle)
        self.storeResource(script, skipCooking=skipCooking)

    security.declareProtected(permissions.ManagePortal, 'updateScript')
    def updateScript(self, id, **data):
        script = self.getResourcesDict().get(id, None)
        if script is None:
            raise ValueError('Invalid resource id %s' % (id))
        if data.get('expression', None) is not None:
            script.setExpression(data['expression'])
        if data.get('authenticated', None) is not None:
            script.setAuthenticated(data['authenticated'])
        if data.get('inline', None) is not None:
            script.setInline(data['inline'])
        if data.get('enabled', None) is not None:
            script.setEnabled(data['enabled'])
        if data.get('cookable', None) is not None:
            script.setCookable(data['cookable'])
        if data.get('compression', None) is not None:
            script.setCompression(data['compression'])
        if data.get('cacheable', None) is not None:
            script.setCacheable(data['cacheable'])
        if data.get('conditionalcomment',None) is not None:
            script.setConditionalcomment(data['conditionalcomment'])
        if data.get('bundle', None) is not None:
            script.setBundle(data['bundle'])

    security.declareProtected(permissions.ManagePortal, 'getCompressionOptions')
    def getCompressionOptions(self):
        """Compression methods for use in ZMI forms."""
        return config.JS_COMPRESSION_METHODS
    
    security.declareProtected(permissions.ManagePortal, 'getExternalCompressionOptions')
    def getExternalCompressionOptions(self):
        """Compression methods for use in ZMI forms."""
        return config.JS_EXTERNAL_COMPRESSION_METHODS

    security.declareProtected(permissions.View, 'getContentType')
    def getContentType(self):
        """Return the registry content type."""
        return 'application/x-javascript;charset=utf-8'

    security.declarePrivate('getResourceContent')
    def getResourceContent(self, item, context, original=False, theme=None):
        output = BaseRegistryTool.getResourceContent(self, item, context, original, theme)
        if not original:
            mapper = JavascriptKeywordMapper()
            regexp = re.compile(r"/\* sTART eNCODE \*/\s*(.*?)\s*/\* eND eNCODE \*/", re.DOTALL)
            matches = regexp.findall(output)
            if len(matches) > 0:
                mapper.analyse("\n".join(matches))
                decoder = mapper.getDecodeFunction(name='__dEcOdE')
                def repl(m):
                    return mapper.getDecoder(mapper.sub(m.group(1)),
                                             keyword_var="''",
                                             decode_func='__dEcOdE')
                #output = "\n__sTaRtTiMe = new Date()\n%s\n%s\nalert(new Date() - __sTaRtTiMe);" % (decoder,
                output = "\n%s\n%s\n" % (decoder,
                                         regexp.sub(repl, output))
        return output

InitializeClass(JSRegistryTool)
