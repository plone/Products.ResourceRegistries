import transaction
from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
from Products.PloneTestCase.layer import onsetup
from Products.Five.zcml import load_config

PloneTestCase.setupPloneSite()

@onsetup
def load_zcml():
    import Products.ResourceRegistries.tests
    load_config('test.zcml', Products.ResourceRegistries.tests)
    
    site = ZopeTestCase.app().plone
    tool = site.portal_setup
    profile_id = 'profile-Products.ResourceRegistries.tests:test'
    result = tool.runImportStepFromProfile(profile_id, 'skins')
    transaction.commit()
load_zcml()

class RegistryTestCase(PloneTestCase.PloneTestCase):
    pass

class FunctionalRegistryTestCase(PloneTestCase.FunctionalTestCase):
    pass
