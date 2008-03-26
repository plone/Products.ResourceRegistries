import unittest
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool

class BaseRegistryTestCase(unittest.TestCase):
    def __init__(self):
        unittest.TestCase.__init__(self)
        self.registry = BaseRegistryTool()

    # Make sure we don't generate an id that could screw up traversal to
    # the cached resource.
    def testGenerateId(self):
        self.failIf('++' in self.registry.generateId('++resource++foobar.css'))
        self.failIf('/' in self.registry.generateId('++resource++foo/bar.css'))

    def runTest(self):
        self.testGenerateId()

def test_suite():
    suite = unittest.TestSuite()

    suite.addTest(BaseRegistryTestCase())

    return suite


