from Products.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.layer import onsetup
from Products.Five.zcml import load_config
from Products.Five import fiveconfigure

@onsetup
def setupPackage():
    fiveconfigure.debug_mode = True
    import Products.ResourceRegistries.tests
    load_config('test.zcml', Products.ResourceRegistries.tests)
    fiveconfigure.debug_mode = False

setupPackage()

PloneTestCase.setupPloneSite(extension_profiles=(
    'Products.ResourceRegistries.tests:test',
))


class RegistryTestCase(PloneTestCase.PloneTestCase):
    pass

class FunctionalRegistryTestCase(RegistryTestCase, FunctionalTestCase):
    pass
