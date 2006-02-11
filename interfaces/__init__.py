from registries import IResourceRegistry, ICSSRegistry, IJSRegistry
import ResourceRegistries

# create zope2 interfaces at runtime:
from Interface.bridge import createZope3Bridge
createZope3Bridge(IResourceRegistry, ResourceRegistries, 'IResourceRegistry')
createZope3Bridge(ICSSRegistry, ResourceRegistries, 'ICSSRegistry')
createZope3Bridge(IJSRegistry, ResourceRegistries, 'IJSRegistry')
