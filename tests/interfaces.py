
from zope.interface import Interface

class IPortal(Interface):
    'The portal root'
    pass
        
class IPortalObject(Interface):
    'All portal objects'
    pass

class IReindexable(Interface):
    def reindexObject():
        '''update catalogs'''
