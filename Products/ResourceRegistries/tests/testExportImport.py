from Products.ResourceRegistries.tests.RegistryTestCase import RegistryTestCase


class TestExportImport(RegistryTestCase):

    def test_removing(self):
        # Test that you can tell the resource registries to remove a
        # resource (a javascript here) using xml.
        from Products.Five.zcml import load_config
        import Products.ResourceRegistries.tests
        load_config('test.zcml', Products.ResourceRegistries.tests)
        tool = self.portal.portal_setup
        profile_id = 'profile-Products.ResourceRegistries.tests:test'
        # The next line used to throw an UnboundLocalError:
        try:
            result = tool.runImportStepFromProfile(profile_id, 'jsregistry')
        except UnboundLocalError, e:
            self.fail("UnboundLocalError thrown: %s" % e)
        assert("resourceregistry: Javascript registry imported." in \
                   result['messages']['jsregistry'],
               "Javascript registry should have been imported")
        # We depend on some other steps:
        self.assertEqual(result['steps'],
                         [u'toolset', u'componentregistry', 'jsregistry'])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestExportImport))

    return suite
