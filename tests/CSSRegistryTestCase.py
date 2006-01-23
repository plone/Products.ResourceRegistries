from Testing import ZopeTestCase

# Make the boring stuff load quietly
ZopeTestCase.installProduct('CMFCore', quiet=1)
ZopeTestCase.installProduct('CMFDefault', quiet=1)
ZopeTestCase.installProduct('CMFCalendar', quiet=1)
ZopeTestCase.installProduct('CMFTopic', quiet=1)
ZopeTestCase.installProduct('DCWorkflow', quiet=1)
ZopeTestCase.installProduct('CMFActionIcons', quiet=1)
ZopeTestCase.installProduct('CMFQuickInstallerTool', quiet=1)
ZopeTestCase.installProduct('CMFFormController', quiet=1)
ZopeTestCase.installProduct('GroupUserFolder', quiet=1)
ZopeTestCase.installProduct('ZCTextIndex', quiet=1)
ZopeTestCase.installProduct('ExtendedPathIndex')
ZopeTestCase.installProduct('ExternalEditor')
ZopeTestCase.installProduct('kupu')

ZopeTestCase.installProduct('CMFPlone')
ZopeTestCase.installProduct('ResourceRegistries')
ZopeTestCase.installProduct('Five')

from Products.PloneTestCase import PloneTestCase

PRODUCTS = ['ResourceRegistries']

ZopeTestCase.utils.setupCoreSessions()
PloneTestCase.setupPloneSite(products=PRODUCTS)

class CSSRegistryTestCase(ZopeTestCase.Functional, PloneTestCase.PloneTestCase):

    class Session(dict):
        def set(self, key, value):
            self[key] = value

    def _setup(self):
        PloneTestCase.PloneTestCase._setup(self)
