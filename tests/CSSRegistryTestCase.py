from Testing import ZopeTestCase

ZopeTestCase.installProduct('ResourceRegistries')
#ZopeTestCase.installProduct('Five')

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
