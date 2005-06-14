from DateTime import DateTime
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import IJSRegistry
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool


class JSRegistryTool(BaseRegistryTool):
    """A Plone registry for managing the linking to Javascript files."""

    id = config.JSTOOLNAME
    meta_type = config.JSTOOLTYPE
    title = 'JavaScript Registry'

    security = ClassSecurityInfo()

    __implements__ = (BaseRegistryTool.__implements__, IJSRegistry)

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

    #
    # Private Methods
    #

    def __init__(self):
        """Initialize Javascript Registry."""
        BaseRegistryTool.__init__(self)
        self.attributes_to_compare = ('expression', 'inline')
        self.filename_base = 'ploneScripts'
        self.filename_appendix = '.js'
        self.cache_duration = config.JS_CACHE_DURATION
        self.merged_output_prefix = """/* Merged Plone Javascript file
 * This file is dynamically assembled from separate parts.
 * Some of these parts have 3rd party licenses or copyright information attached
 * Such information is valid for that section,
 * not for the entire composite file
 * originating files are separated by ----- filename.js -----
 */
"""

    #
    # ZMI Methods
    #

    security.declareProtected(permissions.ManagePortal, 'manage_addScript')
    def manage_addScript(self, id, expression='', inline=False,
                         enabled=True, REQUEST=None):
        """Register a script from a TTW request."""
        self.registerScript(id, expression, inline, enabled)
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
            script = {}
            script['id'] = r.get('id')
            script['expression'] = r.get('expression', '')
            script['inline'] = r.get('inline')
            script['enabled'] = r.get('enabled')
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
    def registerScript(self, id, expression='', inline=False, enabled=True):
        """Register a script."""
        script = {}
        script['id'] = id
        script['expression'] = expression
        script['inline'] = inline
        script['enabled'] = enabled
        self.storeResource(script)

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


InitializeClass(JSRegistryTool)
