#
# CSSRegistryTestCase 
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CSSRegistry.tests import CSSRegistryTestCase

from Products.CSSRegistry.config import JSJSTOOLNAME
from Products.CSSRegistry.interfaces import IJSRegistry
from Interface.Verify import verifyObject

class TestImplementation(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        pass

    def test_interfaces(self):
        tool = getattr(self.portal, JSTOOLNAME)
        self.failUnless(IJSRegistry.isImplementedBy(tool))
        self.failUnless(verifyObject(IJSRegistry, tool))

class TestTool(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        pass

    def testToolExists(self):
        self.failUnless(JSTOOLNAME in self.portal.objectIds())
        
    def testZMIForm(self):
        tool = getattr(self.portal, JSTOOLNAME)
        self.setRoles(['Manager'])
        self.failUnless(tool.manage_cssForm())
        

class TestSkin(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        pass

    def testSkins(self):
        skins = self.portal.portal_skins.objectIds()
        self.failUnless('CSSRegistry' in skins) 

    def testSkinExists(self):
        self.failUnless(getattr(self.portal, 'simple.css' ))


class testZMIMethods(CSSRegistryTestCase.CSSRegistryTestCase):
    
    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
                             
                
    def testAdd(self):
        self.tool.manage_addScript(id='joe')
        self.assertEqual(len(self.tool.getScripts()),1)
        self.failUnless(self.tool.getScripts())
 

class TestScriptRegistration(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)

    def testStoringScript(self):
        self.tool.registerScript('foo')
        
        self.assertEqual(len(self.tool.getScripts()), 1)
        self.assertEqual(self.tool.getScripts()[0].get('id'), 'foo')

    def testDisallowingDuplicateIds(self):
        self.tool.registerScript('foo')
        self.assertRaises(ValueError , self.tool.registerScript , 'foo')
        
    def testPloneCustomStaysOnTop(self):

        self.tool.registerScript('foo')        
        self.tool.registerScript('ploneCustom.css')
        self.assertEqual(len(self.tool.getScripts()), 2)
        self.assertEqual(self.tool.getScripts()[0].get('id'), 'ploneCustom.css')
        self.assertEqual(self.tool.getScripts()[1].get('id'), 'foo')

    def testUnregisterScript(self):
        self.tool.registerScript('foo')        
        self.assertEqual(len(self.tool.getScripts()), 1)
        self.assertEqual(self.tool.getScripts()[0].get('id'), 'foo')
        self.tool.unregisterScript('foo')
        self.assertEqual(len(self.tool.getScripts()), 0)
        
class TestToolSecurity(CSSRegistryTestCase.CSSRegistryTestCase):
    
    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)

    def testRegistrationSecurity(self):
        from AccessControl import Unauthorized
        self.assertRaises(Unauthorized, self.tool.restrictedTraverse , 'registerScript')        
        self.assertRaises(Unauthorized, self.tool.restrictedTraverse , 'unregisterScript')        
        self.setRoles(['Manager'])
        try:
            self.tool.restrictedTraverse('registerScript')  
            self.tool.restrictedTraverse('unregisterScript')  
        except Unauthorized:
            self.fail()      


class TestToolExpression(CSSRegistryTestCase.CSSRegistryTestCase):
    
    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)

    def testSimplestExpression(self):
        context = self.portal
        self.failUnless(self.tool.evaluateExpression('python:1', context ))
        self.failIf(self.tool.evaluateExpression('python:0', context ))
        self.failUnless(self.tool.evaluateExpression('python:0+1', context ))

    def testNormalExpression(self):
        context = self.portal
        self.failUnless(self.tool.evaluateExpression('object/absolute_url', context ))

    def testExpressionInFolder(self):
        self.folder.invokeFactory('Document', 'eggs')
        context = self.folder
        self.failUnless(self.tool.evaluateExpression('python:"eggs" in object.objectIds()', context ))
        
class TestScriptCooking(CSSRegistryTestCase.CSSRegistryTestCase):
    
    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        
    def testScriptCooking(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
                
        self.assertEqual(len(self.tool.getScripts()), 3)
        self.assertEqual(len(self.tool.cookedscripts), 1)
        self.assertEqual(len(self.tool.concatenatedscripts.keys()), 4)

    def testScriptCookingValues(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')

        self.assertEqual(self.tool.concatenatedscripts[self.tool.cookedscripts[0].get('id')], ['eggs', 'spam', 'ham'] )
        
        
    def testGetEvaluatedScriptsCollapsing(self ):        
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(len(self.tool.getEvaluatedScripts(self.folder)) , 1 )

    def testMoreComplexScriptsCollapsing(self ):        
        self.tool.registerScript('ham')
        self.tool.registerScript('spam',           media='spam')
        self.tool.registerScript('spam spam',      media='spam')
        self.tool.registerScript('spam spam spam', media='spam')
        self.tool.registerScript('eggs')
        self.assertEqual(len(self.tool.getEvaluatedScripts(self.folder)) , 3 )
        ids = [item.get('id') for item in self.tool.getEvaluatedScripts(self.folder)]
        self.failUnless('ham' in ids )
        self.failUnless('eggs' in ids )
        self.failIf('spam' in ids )
        self.failIf('spam spam' in ids )
        self.failIf('spam spam spam' in ids )
        
    def testGetEvaluatedScriptsWithExpression(self ):        
        self.tool.registerScript('ham')
        self.tool.registerScript('spam',expression='python:1')
        self.assertEqual(len(self.tool.getEvaluatedScripts(self.folder)), 2 )

    def testGetEvaluatedScriptsWithFailingExpression(self ):        
        self.tool.registerScript('ham')
        self.tool.registerScript('spam',expression='python:0')
        self.assertEqual(len(self.tool.getEvaluatedScripts(self.folder)), 1 )

    def testGetEvaluatedScriptsWithContextualExpression(self ):
        self.folder.invokeFactory('Document', 'eggs')
        self.tool.registerScript('spam',expression='python:"eggs" in object.objectIds()')
        self.assertEqual(len(self.tool.getEvaluatedScripts(self.folder)), 1 )

    def testCollapsingScriptsLookup(self):        
        self.tool.registerScript('ham')
        self.tool.registerScript('spam',           media='spam')
        self.tool.registerScript('spam spam',      media='spam')
        evaluated = self.tool.getEvaluatedScripts(self.folder)
        self.assertEqual(len(evaluated), 2)
        
    def testRenderingIsInTheRightOrder(self):
        self.tool.registerScript('ham' , media='ham')
        self.tool.registerScript('spam', media='spam')
        evaluated = self.tool.getEvaluatedScripts(self.folder)
        evaluatedids = [item['id'] for item in evaluated]
        self.failUnless(evaluatedids[1]=='spam')
        self.failUnless(evaluatedids[0]=='ham')
        
        # can you tell we had good fun writing these tests ? 
        
    def testRenderingScriptLinks(self):        
        self.tool.registerScript('ham')
        self.tool.registerScript('ham 2 b merged')
        self.tool.registerScript('spam', media='print')
        self.tool.registerScript('simple.css', inline='1')
        all = getattr(self.portal, 'renderAllTheScripts')()
        self.failUnless('background-color' in all)
        self.failUnless('<link' in all)
        self.failUnless('/spam' in all)
        
    def testReenderingConcatenatesInline(self):
        self.tool.registerScript('simple.css', inline='1')
        self.tool.registerScript('simple2.css', inline='1')
        all = getattr(self.portal, 'renderAllTheScripts')()
        self.failUnless('background-color' in all)
        self.failUnless('blue' in all)        
        
    def testRenderingWorksInMainTemplate(self):

        renderedpage = getattr(self.portal, 'index_html')()
        self.failIf('background-color' in renderedpage)
        
        self.tool.registerScript('simple.css', inline=1)
        
        renderedpage = getattr(self.portal, 'index_html')()
        self.failUnless('background-color' in renderedpage)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestImplementation))
    suite.addTest(makeSuite(TestTool))
    suite.addTest(makeSuite(TestSkin))
    suite.addTest(makeSuite(testZMIMethods))
    suite.addTest(makeSuite(TestScriptRegistration))
    suite.addTest(makeSuite(TestToolSecurity))
    suite.addTest(makeSuite(TestToolExpression))
    suite.addTest(makeSuite(TestScriptCooking))
    return suite

if __name__ == '__main__':
    framework()
