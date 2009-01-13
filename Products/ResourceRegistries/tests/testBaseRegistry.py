import unittest
from Products.ResourceRegistries.tools.BaseRegistry import BaseRegistryTool, Resource

class BaseRegistryTestCase(unittest.TestCase):
    def __init__(self):
        unittest.TestCase.__init__(self)
        self.registry = BaseRegistryTool()

    # Make sure we don't generate an id that could screw up traversal to
    # the cached resource.
    def testGenerateId(self):
        self.failIf('++' in self.registry.generateId('++resource++foobar.css'))
        self.failIf('/' in self.registry.generateId('++resource++foo/bar.css'))
    
    #Resources with double //'s in them aren't traversable. The page templates
    # assume that no resource will have a '/' at the start or end, and won't
    # have a '//' anywhere inside. A single '/' inside is fine.
    def testTraversableResourceID(self):
        ids = {'/bar.res': False, #expected to fail
               'bar.res' : True,  #expected to pass
               'bar.//res' : False, #expected to fail
               'bar.res/' : False, #expected to fail
               'foo/bar.res' : True, #perfectly fine
               'http://example.com/example.res' : True, #This should work now
               }
        for id in ids:
            if ids[id]: #This shouldn't error
                res = Resource(id)
            else: #This should throw a ValueError
                self.failUnlessRaises(ValueError,Resource,id)
                self.assertRaises(ValueError,Resource,id)

    def runTest(self):
        self.testGenerateId()
        self.testTraversableResourceID()

def test_suite():
    suite = unittest.TestSuite()

    suite.addTest(BaseRegistryTestCase())

    return suite


