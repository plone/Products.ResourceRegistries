#
# CSSRegistryTestCase 
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CSSRegistry.tests import CSSRegistryTestCase

from Products.CSSRegistry.config import JSTOOLNAME
from Products.CSSRegistry.interfaces import IJSRegistry
from Interface.Verify import verifyObject

from Products.PloneTestCase.PloneTestCase import PLONE21        

class TestJSImplementation(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        pass

    def test_interfaces(self):
        tool = getattr(self.portal, JSTOOLNAME)
        self.failUnless(IJSRegistry.isImplementedBy(tool))
        self.failUnless(verifyObject(IJSRegistry, tool))

class TestJSTool(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        pass

    def testToolExists(self):
        self.failUnless(JSTOOLNAME in self.portal.objectIds())
        
    def testZMIForm(self):
        tool = getattr(self.portal, JSTOOLNAME)
        self.setRoles(['Manager'])
        self.failUnless(tool.manage_jsForm())
        

class TestJSSkin(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        pass

    def testSkins(self):
        skins = self.portal.portal_skins.objectIds()
        self.failUnless('CSSRegistry' in skins) 

    def testSkinExists(self):
        self.failUnless(getattr(self.portal, 'renderAllTheScripts' ))
                                           

class testJSZMIMethods(CSSRegistryTestCase.CSSRegistryTestCase):
    
    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.scripts = []    
                
    def testAdd(self):
        self.tool.manage_addScript(id='joe')
        self.assertEqual(len(self.tool.getScripts()),1)
        self.failUnless(self.tool.getScripts())
 

class TestJSScriptRegistration(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.scripts = []    


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
        
class TestJSToolSecurity(CSSRegistryTestCase.CSSRegistryTestCase):
    
    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.scripts = []    

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


class TestJSToolExpression(CSSRegistryTestCase.CSSRegistryTestCase):
    
    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.scripts = []    

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
        
class TestJSScriptCooking(CSSRegistryTestCase.CSSRegistryTestCase):
    
    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.scripts = []    
        
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
        self.tool.registerScript('spam',           expression='string:spam')
        self.tool.registerScript('spam spam',      expression='string:spam')
        self.tool.registerScript('spam spam spam', expression='string:spam')
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
        self.tool.registerScript('spam',           expression='string:spam')
        self.tool.registerScript('spam spam',      expression='string:spam')
        evaluated = self.tool.getEvaluatedScripts(self.folder)
        self.assertEqual(len(evaluated), 2)
        
    def testRenderingIsInTheRightOrder(self):
        self.tool.registerScript('ham' , expression='string:ham')
        self.tool.registerScript('spam', expression='string:spam')
        evaluated = self.tool.getEvaluatedScripts(self.folder)
        evaluatedids = [item['id'] for item in evaluated]
        self.failUnless(evaluatedids[1]=='spam')
        self.failUnless(evaluatedids[0]=='ham')
        
        # can you tell we had good fun writing these tests ? 
        
    def testRenderingScriptLinks(self):        
        self.tool.registerScript('ham')
        self.tool.registerScript('ham2merge')
        self.tool.registerScript('spam', expression='string:spam')
        self.tool.registerScript('simple.css', inline='1')
        all = getattr(self.portal, 'renderAllTheScripts')()
        self.failUnless('background-color' in all)
        self.failUnless('<script' in all)
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

class TestJSTraversal(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.scripts = []    
        self.tool.registerScript('simple.css')

    def testGetItemTraversal(self):
        self.failUnless(self.tool['simple.css'])
        
    def testGetItemTraversalContent(self):
        self.failUnless('background-color' in str(self.tool['simple.css']))
        
    def testRestrictedTraverseContent(self):
        self.failUnless('background-color' in str(self.portal.restrictedTraverse('portal_javascripts/simple.css')))


    def testRestricedTraverseComposition(self):
        self.tool.registerScript('simple2.css')
        scripts = self.tool.getEvaluatedScripts(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].get('id')
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        self.failUnless('background-color' in content)
        self.failUnless('blue' in content)

    def testCompositesWithBrokedId(self):
        self.tool.registerScript('nonexistant.css')
        scripts = self.tool.getEvaluatedScripts(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].get('id')
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        print content

class TestJSDefaults(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
    
    def testClearingScripts(self):
        self.failUnless(self.tool.getScripts())
        self.tool.clearScripts()
        self.failIf(self.tool.getScripts())   
    
    def testDefaultsInstall(self):
        scriptids = [item['id'] for item in self.tool.getScripts()]
        self.failUnless('plone_menu.js' in scriptids)
        self.failUnless('plone_javascript_variables.js' in scriptids)
        self.failUnless('plone_javascripts.js' in scriptids)

    def testTraverseToConcatenatedDefaults(self):
        scripts = self.tool.getEvaluatedScripts(self.portal)
        for s in scripts:
            try:
                magicId = s.get('id')
                self.portal.restrictedTraverse('portal_javascripts/%s' % magicId)
            except KeyError:
                self.fail()

    def testUserConditionOnMenuScript(self):
        scripts1 = self.tool.getEvaluatedScripts(self.portal)
        self.logout()
        scripts2 = self.tool.getEvaluatedScripts(self.portal)
        self.failUnless(len(scripts1) > len(scripts2))
                
    def testCallingOfConcatenatedScripts(self):     
        stylesheets = self.tool.getEvaluatedScripts(self.portal)
        for s in stylesheets:
            if 'ploneScripts' in s.get('id'):
                output = self.portal.restrictedTraverse('portal_javascripts/%s' % s.get('id'))
                break
        if not output:
            self.fail()
        o = str(output)[:]
        self.failIf("&lt;dtml-call" in o)            
        self.failIf("&amp;dtml" in o)            
        self.failUnless('portal_url' in o)            
        
                
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestJSImplementation))
    suite.addTest(makeSuite(TestJSTool))
    suite.addTest(makeSuite(TestJSSkin))
    suite.addTest(makeSuite(testJSZMIMethods))
    suite.addTest(makeSuite(TestJSScriptRegistration))
    suite.addTest(makeSuite(TestJSToolSecurity))
    suite.addTest(makeSuite(TestJSToolExpression))
    suite.addTest(makeSuite(TestJSScriptCooking))
    suite.addTest(makeSuite(TestJSTraversal))

    if not PLONE21:
        # we must not test for the defaults in Plone 2.1 because they are all different
        # Plone2.1 has tests in CMFPlone/tests for defaults and migrations
        suite.addTest(makeSuite(TestJSDefaults))


    return suite

if __name__ == '__main__':
    framework()
