from Products.ResourceRegistries.interfaces import ICSSRegistry

from resourceregistry import ResourceRegistryNodeAdapter, \
     importResRegistry, exportResRegistry

_FILENAME = 'cssregistry.xml'
_REG_ID = 'portal_css'
_REG_TITLE = 'Stylesheet registry'

def importCSSRegistry(context):
    """
    Import javascript registry.
    """
    return importResRegistry(context, _REG_ID, _REG_TITLE, _FILENAME)

def exportCSSRegistry(context):
    """
    Export javascript registry.
    """
    return exportResRegistry(context, _REG_ID, _REG_TITLE, _FILENAME)


class CSSRegistryNodeAdapter(ResourceRegistryNodeAdapter):
    """
    Node im- and exporter for CSSRegistry.
    """

    __used_for__ = ICSSRegistry
    registry_id = _REG_ID
    resource_type = 'stylesheet'
    register_method = 'registerStylesheet'
