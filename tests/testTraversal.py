#
# CSSRegistryTestCase Skeleton
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CSSRegistry.tests import CSSRegistryTestCase
from Products.CSSRegistry.config import TOOLNAME


class TestTraversal(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, TOOLNAME)
        self.tool.registerStylesheet('simple.css')

    def testGetItemTraversal(self):
        self.failUnless(self.tool['simple.css'])
        
    def testGetItemTraversalContent(self):
        self.failUnless('background-color' in str(self.tool['simple.css']))
        
    def testRestrictedTraverseContent(self):
        self.failUnless('background-color' in str(self.portal.restrictedTraverse('portal_css/simple.css')))


    def testRestricedTraverseComposition(self):
        self.tool.registerStylesheet('simple2.css')
        styles = self.tool.getEvaluatedStylesheets(self.portal)
        self.assertEqual(len(styles), 1)
        magicId = styles[0].get('id')
        
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicId))
        self.failUnless('background-color' in content)
        self.failUnless('blue' in content)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTraversal))
    return suite

if __name__ == '__main__':
    framework()
