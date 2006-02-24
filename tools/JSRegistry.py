from DateTime import DateTime
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.interface import implements

from Products.CMFCore.utils import getToolByName

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces.ResourceRegistries import IJSRegistry as z2IJSRegistry
from Products.ResourceRegistries.interfaces import IJSRegistry
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool
from Products.ResourceRegistries.tools.BaseRegistry import Resource

import re
from packer import Packer
try:
    from jspacker import JavaScriptPacker
    JSPACKER = True
except ImportError:
    JSPACKER = False


jspacker = Packer()
# protect strings
jspacker.protect(r"""'(?:\\'|.|\\\n)*?'""")
jspacker.protect(r'''"(?:\\"|.|\\\n)*?"''')
# protect regular expressions
jspacker.protect(r"""\s+(\/[^\/\n\r\*][^\/\n\r]*\/g?i?)""")
jspacker.protect(r"""[^\w\$\/'"*)\?:]\/[^\/\n\r\*][^\/\n\r]*\/g?i?""")
# strip whitespace
jspacker.sub(r'^[ \t\r\f\v]*(.*?)[ \t\r\f\v]*$', r'\1', re.MULTILINE)
# multiline comments
jspacker.sub(r'/\*.*?\*/', '', re.DOTALL)
# one line comments
jspacker.sub(r'\s*//.*$', '', re.MULTILINE)
# whitespace after some special chars but not
# before function declaration
jspacker.sub(r'([{;\[(,=&|\?:])\s+(?!function)', r'\1')
# whitespace before some special chars
jspacker.sub(r'\s+([{}\],=&|\?:)])', r'\1')
# whitespace before plus chars if no other plus char before it
jspacker.sub(r'(?<!\+)\s+\+', '+')
# whitespace after plus chars if no other plus char after it
jspacker.sub(r'\+\s+(?!\+)', '+')
# whitespace before minus chars if no other minus char before it
jspacker.sub(r'(?<!-)\s+-', '-')
# whitespace after minus chars if no other minus char after it
jspacker.sub(r'-\s+(?!-)', '-')
# remove any excessive whitespace left except newlines
jspacker.sub(r'[ \t\r\f\v]+', ' ')
# excessive newlines
jspacker.sub(r'\n+', '\n')
# first newline
jspacker.sub(r'^\n', '')

jspacker_full = jspacker.copy()
# encode local variables. those are preceeded by dollar signs
# the amount of dollar signs says how many characters are preserved
# $name -> n, $$name -> na
def _dollar_replacement(match):
    length = len(match.group(2))
    start = length - max(length - len(match.group(3)), 0)
    return match.group(1)[start:start+length] + match.group(4)
jspacker_full.sub(r"""((\$+)([a-zA-Z\$_]+))(\d*)""", _dollar_replacement)


class JavaScript(Resource):
    security = ClassSecurityInfo()

    def __init__(self, id, **kwargs):
        Resource.__init__(self, id, **kwargs)
        self._data['inline'] = kwargs.get('inline', False)
        self._data['compression'] = kwargs.get('compression', 'safe')

    security.declarePublic('getInline')
    def getInline(self):
        return self._data['inline']

    security.declareProtected(permissions.ManagePortal, 'setInline')
    def setInline(self, inline):
        self._data['inline'] = inline

    security.declarePublic('getCompression')
    def getCompression(self):
        # as this is a new property, old instance might not have that value, so
        # return 'safe' as default
        compression = self._data.get('compression', 'safe')
        if compression in ['safe','full']:
            return compression
        return 'none'

    security.declareProtected(permissions.ManagePortal, 'setCompression')
    def setCompression(self, compression):
        self._data['compression'] = compression

InitializeClass(JavaScript)


class JSRegistryTool(BaseRegistryTool):
    """A Plone registry for managing the linking to Javascript files."""

    id = config.JSTOOLNAME
    meta_type = config.JSTOOLTYPE
    title = 'JavaScript Registry'

    security = ClassSecurityInfo()

    implements(IJSRegistry)
    __implements__ = (BaseRegistryTool.__implements__, z2IJSRegistry)

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

    attributes_to_compare = ('getExpression', 'getCookable',
                             'getCacheable', 'getInline')
    filename_base = 'ploneScripts'
    filename_appendix = '.js'
    cache_duration = config.JS_CACHE_DURATION
    merged_output_prefix = """
/* Merged Plone Javascript file
 * This file is dynamically assembled from separate parts.
 * Some of these parts have 3rd party licenses or copyright information attached
 * Such information is valid for that section,
 * not for the entire composite file
 * originating files are separated by ----- filename.js -----
 */
"""
    resource_class = JavaScript

    #
    # Private Methods
    #

    security.declarePrivate('clearScripts')
    def clearScripts(self):
        self.clearResources()

    def _compressJS(self, content, level='safe'):
        if level == 'full':
            return jspacker_full.pack(content)
        elif level == 'safe':
            return jspacker.pack(content)
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
                         REQUEST=None):
        """Register a script from a TTW request."""
        self.registerScript(id, expression, inline, enabled, cookable, compression)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_saveScripts')
    def manage_saveScripts(self, REQUEST=None):
        """Save scripts from the ZMI.

        Updates the whole sequence. For editing and reordering.
        """
        debugmode = REQUEST.get('debugmode',False)
        self.setDebugMode(debugmode)
        records = REQUEST.form.get('scripts')
        records.sort(lambda a, b: a.sort-b.sort)
        self.resources = ()
        scripts = []
        for r in records:
            script = JavaScript(r.get('id'),
                                expression=r.get('expression', ''),
                                inline=r.get('inline'),
                                enabled=r.get('enabled'),
                                cookable=r.get('cookable'),
                                cacheable=r.get('cacheable'),
                                compression=r.get('compression'))
            scripts.append(script)
        self.resources = tuple(scripts)
        self.cookResources()
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'manage_removeScript')
    def manage_removeScript(self, id, REQUEST=None):
        """Remove script with ZMI button."""
        self.unregisterResource(id)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    #
    # Protected Methods
    #

    security.declareProtected(permissions.ManagePortal, 'registerScript')
    def registerScript(self, id, expression='', inline=False, enabled=True,
                       cookable=True, compression='safe'):
        """Register a script."""
        script = JavaScript(id,
                            expression=expression,
                            inline=inline,
                            enabled=enabled,
                            cookable=cookable)
        self.storeResource(script)

    security.declareProtected(permissions.ManagePortal, 'getCompressionOptions')
    def getCompressionOptions(self):
        """Compression methods for use in ZMI forms."""
        return config.JS_COMPRESSION_METHODS

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
        return 'application/x-javascript;charset=%s' % encoding

    security.declarePrivate('getResourceContent')
    def getResourceContent(self, item, context, original=False):
        output = BaseRegistryTool.getResourceContent(self, item, context, original)
        if JSPACKER and not original:
            packer = JavaScriptPacker()
            result = packer.pack(output, compaction=False, encoding=62, fastDecode=True)
            if len(result) < len(output):
                return result
        return output

InitializeClass(JSRegistryTool)
