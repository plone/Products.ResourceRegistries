from Products.PloneTestCase import PloneTestCase

PloneTestCase.setupPloneSite(extension_profiles=['Products.CMFPlone:testfixture'])

class RegistryTestCase(PloneTestCase.PloneTestCase):
    pass

class FunctionalRegistryTestCase(PloneTestCase.FunctionalTestCase,
                                 PloneTestCase.PloneTestCase):
    pass
