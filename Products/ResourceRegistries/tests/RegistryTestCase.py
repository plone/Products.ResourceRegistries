from App.Common import rfc1123_date
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

    from Products.CMFCore.DirectoryView import registerFileExtension
    from Products.CMFCore.FSFile import FSFile
    registerFileExtension('kss', FSFile)


setupPackage()

PloneTestCase.setupPloneSite(extension_profiles=(
    'Products.ResourceRegistries.tests:test',
))


class RegistryTestCase(PloneTestCase.PloneTestCase):

    def assertExpiresEqual(self, expires, moment):
        """Assert that the Expires header is equal to a moment or one
        second earlier or later.

        Should work for other headers too, but Expires is the most
        common, at least in these tests.

        There are some spurious test failures because 'now' is
        calculated, then a request is made and some headers are set,
        but this takes slightly too long and the resulting Expires
        header is one second after 'now'.

        - expires: usually response.getHeader('Expires')

        - moment: number of seconds, usually DateTime().timeTime().
          NOT an rfc1123 date
        """
        if expires == rfc1123_date(moment):
            return
        if expires == rfc1123_date(moment + 1):
            return
        if expires == rfc1123_date(moment - 1):
            return
        # We have a failure.  Call the method that would originally be
        # called.
        self.assertEqual(expires, rfc1123_date(moment))

    def assertExpiresNotEqual(self, expires, moment):
        """Assert that the Expires header is NOT equal to a moment or one
        second earlier or later.

        There are some spurious test failures because 'now' is
        calculated, then a request is made and some headers are set,
        but this takes slightly too long and the resulting Expires
        header is one second after 'now'.

        - expires: usually response.getHeader('Expires')

        - moment: number of seconds, usually DateTime().timeTime().
          NOT an rfc1123 date
        """
        if expires != rfc1123_date(moment) and \
                expires != rfc1123_date(moment + 1) and \
                expires != rfc1123_date(moment - 1):
            return
        # We have a failure.  Call the method that would originally be
        # called.
        self.assertNotEqual(expires, rfc1123_date(moment))


class FunctionalRegistryTestCase(RegistryTestCase, FunctionalTestCase):
    pass
