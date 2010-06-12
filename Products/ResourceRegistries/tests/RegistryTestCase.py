from Products.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.layer import onsetup

# BBB Zope 2.12
try:
    from Zope2.App.zcml import load_config
    from OFS import metaconfigure
except ImportError:
    from Products.Five.zcml import load_config
    from Products.Five import fiveconfigure as metaconfigure

@onsetup
def setupPackage():
    metaconfigure.debug_mode = True
    import Products.ResourceRegistries.tests
    load_config('test.zcml', Products.ResourceRegistries.tests)
    metaconfigure.debug_mode = False

setupPackage()

PloneTestCase.setupPloneSite(extension_profiles=(
    'Products.ResourceRegistries.tests:test',
))


class RegistryTestCase(PloneTestCase.PloneTestCase):
    pass

class FunctionalRegistryTestCase(RegistryTestCase, FunctionalTestCase):
    pass
