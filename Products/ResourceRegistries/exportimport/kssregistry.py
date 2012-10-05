from Products.ResourceRegistries.interfaces import IKSSRegistry

from resourceregistry import ResourceRegistryNodeAdapter, \
     importResRegistry, exportResRegistry

_FILENAME = 'kssregistry.xml'
_REG_ID = 'portal_kss'
_REG_TITLE = 'KSS registry'

def importKSSRegistry(context):
    """
    Import KSS registry.
    """
    portal_kss = context.getSite().get('portal_kss')
    if portal_kss is not None:
        return importResRegistry(context, _REG_ID, _REG_TITLE, _FILENAME)

def exportKSSRegistry(context):
    """
    Export KSS registry.
    """
    portal_kss = context.getSite().get('portal_kss')
    if portal_kss is not None:
        return exportResRegistry(context, _REG_ID, _REG_TITLE, _FILENAME)


class KSSRegistryNodeAdapter(ResourceRegistryNodeAdapter):
    """
    Node im- and exporter for KSSRegistry.
    """

    __used_for__ = IKSSRegistry
    registry_id = _REG_ID
    resource_type = 'kineticstylesheet'
    register_method = 'registerKineticStylesheet'
    update_method = 'updateKineticStylesheet'
