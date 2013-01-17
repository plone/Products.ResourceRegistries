from Products.ResourceRegistries.tests.RegistryTestCase import RegistryTestCase


class TestExportImport(RegistryTestCase):

    def test_removing(self):
        # Test that you can tell the resource registries to remove a
        # resource (a javascript here) using xml.
        tool = self.portal.portal_setup
        profile_id = 'profile-Products.ResourceRegistries.tests:test'
        # The next line used to throw an UnboundLocalError:
        try:
            result = tool.runImportStepFromProfile(profile_id, 'jsregistry')
        except UnboundLocalError, e:
            self.fail("UnboundLocalError thrown: %s" % e)
        self.assertTrue("resourceregistry: Javascript registry imported." in \
                   result['messages']['jsregistry'],
               "Javascript registry should have been imported")
        # We depend on some other steps:
        self.assertEqual(result['steps'],
            [u'skins', u'toolset', u'componentregistry', 'jsregistry'])

    def test_snapshot(self):
        # GenericSetup snapshot should work
        self.setRoles(['Manager'])
        tool = self.portal.portal_setup
        snapshot_id = tool._mangleTimestampName('test')
        tool.createSnapshot(snapshot_id)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestExportImport))

    return suite
