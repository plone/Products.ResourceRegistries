from Products.PloneTestCase.ptc import PloneTestCase, Functional, setupPloneSite

PRODUCTS = ['ResourceRegistries']

setupPloneSite(products=PRODUCTS)

class RegistryTestCase(PloneTestCase):
    pass

class FunctionalRegistryTestCase(Functional, PloneTestCase):
    pass
