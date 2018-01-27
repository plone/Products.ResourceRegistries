from Products.ResourceRegistries.interfaces import ICSSRegistry
from .resourceregistry import exportResRegistry
from .resourceregistry import importResRegistry
from .resourceregistry import ResourceRegistryNodeAdapter


_FILENAME = 'cssregistry.xml'
_REG_ID = 'portal_css'
_REG_TITLE = 'Stylesheet registry'


def importCSSRegistry(context):
    """
    Import CSS registry.
    """
    return importResRegistry(context, _REG_ID, _REG_TITLE, _FILENAME)


def exportCSSRegistry(context):
    """
    Export CSS registry.
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
    update_method = 'updateStylesheet'
