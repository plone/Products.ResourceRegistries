from Products.PloneTestCase import PloneTestCase

PloneTestCase.setupPloneSite()

class RegistryTestCase(PloneTestCase.PloneTestCase):
    pass

class FunctionalRegistryTestCase(PloneTestCase.FunctionalTestCase):
    pass
