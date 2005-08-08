#
# JSRegistry Tests
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from App.Common import rfc1123_date
from DateTime import DateTime
from zExceptions import NotFound
from AccessControl import Unauthorized
from Interface.Verify import verifyObject

from Products.CMFCore.utils import getToolByName

from Products.PloneTestCase.PloneTestCase import PLONE21

from Products.ResourceRegistries.config import JSTOOLNAME
from Products.ResourceRegistries.interfaces import IJSRegistry
from Products.ResourceRegistries.tests import CSSRegistryTestCase


class TestJSImplementation(CSSRegistryTestCase.CSSRegistryTestCase):

    def test_interfaces(self):
        tool = getattr(self.portal, JSTOOLNAME)
        self.failUnless(IJSRegistry.isImplementedBy(tool))
        self.failUnless(verifyObject(IJSRegistry, tool))


class TestJSTool(CSSRegistryTestCase.CSSRegistryTestCase):

    def testToolExists(self):
        self.failUnless(JSTOOLNAME in self.portal.objectIds())

    def testZMIForm(self):
        tool = getattr(self.portal, JSTOOLNAME)
        self.setRoles(['Manager'])
        self.failUnless(tool.manage_jsForm())
        self.failUnless(tool.manage_jsComposition())


class TestJSSkin(CSSRegistryTestCase.CSSRegistryTestCase):

    def testSkins(self):
        skins = self.portal.portal_skins.objectIds()
        self.failUnless('ResourceRegistries' in skins)

    def testSkinExists(self):
        self.failUnless(getattr(self.portal, 'renderAllTheScripts'))


class testJSZMIMethods(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testAdd(self):
        self.tool.manage_addScript(id='joe')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.failUnless(self.tool.getResources())


class TestJSScriptRegistration(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testStoringScript(self):
        self.tool.registerScript('foo')
        self.assertEqual(len(self.tool.getResources()), 1)
        script = self.tool.getResources()[0]
        self.assertEqual(script.getId(), 'foo')
        self.assertEqual(script.getExpression(), '')
        self.assertEqual(script.getInline(), False)
        self.assertEqual(script.getEnabled(), True)

    def testDisallowingDuplicateIds(self):
        self.tool.registerScript('foo')
        self.assertRaises(ValueError, self.tool.registerScript, 'foo')

    def testUnregisterScript(self):
        self.tool.registerScript('foo')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.assertEqual(self.tool.getResources()[0].getId(), 'foo')
        self.tool.unregisterResource('foo')
        self.assertEqual(len(self.tool.getResources()), 0)


class TestJSScriptRenaming(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testRenaming(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])
        self.tool.renameResource('spam', 'bacon')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'bacon', 'eggs'])

    def testRenamingIdClash(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertRaises(ValueError, self.tool.renameResource, 'spam', 'eggs')

    def testDoubleRenaming(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.tool.renameResource('spam', 'bacon')
        self.assertRaises(ValueError, self.tool.renameResource, 'spam', 'bacon')


class TestJSToolSecurity(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testRegistrationSecurity(self):
        self.assertRaises(Unauthorized, self.tool.restrictedTraverse,
                          'registerScript')
        self.assertRaises(Unauthorized, self.tool.restrictedTraverse,
                          'unregisterResource')
        self.setRoles(['Manager'])
        try:
            self.tool.restrictedTraverse('registerScript')
            self.tool.restrictedTraverse('unregisterResource')
        except Unauthorized:
            self.fail()


class TestJSToolExpression(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testSimplestExpression(self):
        context = self.portal
        self.failUnless(self.tool.evaluateExpression('python:1', context))
        self.failIf(self.tool.evaluateExpression('python:0', context))
        self.failUnless(self.tool.evaluateExpression('python:0+1', context))

    def testNormalExpression(self):
        context = self.portal
        self.failUnless(self.tool.evaluateExpression('object/absolute_url',
                                                     context))

    def testExpressionInFolder(self):
        self.folder.invokeFactory('Document', 'eggs')
        context = self.folder
        self.failUnless(self.tool.evaluateExpression(
                        'python:"eggs" in object.objectIds()', context))


class TestJSScriptCooking(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testScriptCooking(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 1)
        self.assertEqual(len(self.tool.concatenatedresources.keys()), 4)

    def testScriptCookingValues(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])

    def testGetEvaluatedScriptsCollapsing(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testMoreComplexScriptsCollapsing(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam', expression='string:spam')
        self.tool.registerScript('spam spam', expression='string:spam')
        self.tool.registerScript('spam spam spam', expression='string:spam')
        self.tool.registerScript('eggs')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 3)
        ids = [item.getId() for item in self.tool.getEvaluatedResources(self.folder)]
        self.failUnless('ham' in ids)
        self.failUnless('eggs' in ids)
        self.failIf('spam' in ids)
        self.failIf('spam spam' in ids)
        self.failIf('spam spam spam' in ids)

    def testGetEvaluatedScriptsWithExpression(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam', expression='python:1')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 2)

    def testGetEvaluatedScriptsWithFailingExpression(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam', expression='python:0')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testGetEvaluatedScriptsWithContextualExpression(self):
        self.folder.invokeFactory('Document', 'eggs')
        self.tool.registerScript('spam', expression='python:"eggs" in object.objectIds()')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testCollapsingScriptsLookup(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam', expression='string:spam')
        self.tool.registerScript('spam spam', expression='string:spam')
        evaluated = self.tool.getEvaluatedResources(self.folder)
        self.assertEqual(len(evaluated), 2)

    def testRenderingIsInTheRightOrder(self):
        self.tool.registerScript('ham', expression='string:ham')
        self.tool.registerScript('spam', expression='string:spam')
        evaluated = self.tool.getEvaluatedResources(self.folder)
        evaluatedids = [item.getId() for item in evaluated]
        self.failUnless(evaluatedids[0] == 'ham')
        self.failUnless(evaluatedids[1] == 'spam')

    def testRenderingScriptLinks(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('ham2merge')
        self.tool.registerScript('spam', expression='string:spam')
        self.tool.registerScript('test_rr_1.css', inline='1')
        all = getattr(self.portal, 'renderAllTheScripts')()
        self.failUnless('background-color' in all)
        self.failUnless('<script' in all)
        self.failUnless('/spam' in all)

    def testReenderingConcatenatesInline(self):
        self.tool.registerScript('test_rr_1.css', inline='1')
        self.tool.registerScript('test_rr_2.css', inline='1')
        all = getattr(self.portal, 'renderAllTheScripts')()
        self.failUnless('background-color' in all)
        self.failUnless('blue' in all)

    def testRenderingWorksInMainTemplate(self):
        renderedpage = getattr(self.portal, 'index_html')()
        self.failIf('background-color' in renderedpage)
        self.tool.registerScript('test_rr_1.css', inline=1)
        renderedpage = getattr(self.portal, 'index_html')()
        self.failUnless('background-color' in renderedpage)


class TestScriptMoving(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testScriptMoveDown(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceDown('ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'ham', 'eggs'))

    def testScriptMoveDownAtEnd(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceDown('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))

    def testScriptMoveUp(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceUp('spam')
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'ham', 'eggs'))

    def testScriptMoveUpAtStart(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceUp('ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))

    def testScriptMoveIllegalId(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.assertRaises(NotFound, self.tool.moveResourceUp, 'foo')

    def testScriptMoveToBottom(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceToBottom('ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'eggs', 'ham'))

    def testScriptMoveToTop(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceToTop('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('eggs', 'ham', 'spam'))

    def testScriptMoveBefore(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.tool.registerScript('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResourceBefore('bacon', 'ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('bacon', 'ham', 'spam', 'eggs'))

    def testScriptMoveAfter(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.tool.registerScript('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResourceAfter('bacon', 'ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'bacon', 'spam', 'eggs'))

    def testScriptMove(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.tool.registerScript('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResource('ham', 2)
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'eggs', 'ham', 'bacon'))
        self.tool.moveResource('bacon', 0)
        self.assertEqual(self.tool.getResourceIds(),
                         ('bacon', 'spam', 'eggs', 'ham'))

class TestJSTraversal(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.tool.registerScript('test_rr_1.js')

    def testGetItemTraversal(self):
        self.failUnless(self.tool['test_rr_1.js'])

    def testGetItemTraversalContent(self):
        self.failUnless('running' in str(
                        self.tool['test_rr_1.js']))

    def testRestrictedTraverseContent(self):
        self.failUnless('running' in str(
                        self.portal.restrictedTraverse(
                            'portal_javascripts/test_rr_1.js')))

    def testRestrictedTraverseComposition(self):
        self.tool.registerScript('test_rr_2.css')
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].getId()
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        # XXX: Review
        #self.failUnless('test_rr_1.js' in content)
        #self.failUnless('registerPloneFunction' in content)

    def testCompositesWithBrokenId(self):
        self.tool.registerScript('nonexistant.js')
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].getId()
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))


class TestPublishing(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)
        self.tool.registerScript('test_rr_1.js')
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'index_html')
        self.setRoles(['Member'])

    def testPublishJSThroughTool(self):
        response = self.publish(self.toolpath + '/test_rr_1.js')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'),
                         'application/x-javascript')

    def testPublishNonMagicJSThroughTool(self):
        self.setRoles(['Manager'])
        body = """<dtml-var "'joined' + 'string'">"""
        self.portal.addDTMLMethod('testmethod', file=body)
        self.tool.registerScript('testmethod')
        response = self.publish(self.toolpath + '/testmethod')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'),
                         'application/x-javascript;charset=utf-8')

    def testPublishPageWithInlineJS(self):
        # This one fails from string/utf-8 concatenation
        response = self.publish(self.portalpath)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.tool.clearResources()
        self.tool.registerScript('test_rr_1.js', inline=True)
        # Test that the main page retains its content-type
        response = self.publish(self.portalpath)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.assertEqual(response.getStatus(), 200)

    def testPublishPageWithInlineJS2(self):
        self.tool.clearResources()
        # Test that the main page retains its content-type
        self.setRoles(['Manager'])
        body = """<dtml-call "REQUEST.RESPONSE.setHeader('Content-Type', 'text/javascript')">/*and some js comments too*/ """
        self.portal.addDTMLMethod('testmethod', file=body)
        self.tool.registerScript('testmethod', inline=True)
        response = self.publish(self.portalpath)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.assertEqual(response.getStatus(), 200)


class TestDebugMode(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)
        self.toolpath = '/' + self.tool.absolute_url(1)

    def testDebugModeSplitting(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)
        self.tool.setDebugMode(True)
        self.tool.cookResources()
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 2)

    def testDebugModeSplitting(self):
        self.tool.registerScript('ham')
        # Publish in normal mode
        response = self.publish(self.toolpath+'/ham')
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Expires'), rfc1123_date(soon.timeTime()))
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

        # Set debug mode
        self.tool.setDebugMode(True)
        self.tool.cookResources()
        # Publish in debug mode
        response = self.publish(self.toolpath+'/ham')
        self.failIfEqual(response.getHeader('Expires'), rfc1123_date(soon.timeTime()))
        self.assertEqual(response.getHeader('Expires'), rfc1123_date(now.timeTime()))
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=0')


class TestJSDefaults(CSSRegistryTestCase.CSSRegistryTestCase):

    # These do not run for plone 2.1 +

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)

    def testClearingScripts(self):
        self.failUnless(self.tool.getResources())
        self.tool.clearResources()
        self.failIf(self.tool.getResources())

    def testDefaultsInstall(self):
        scriptids = self.tool.getResourceIds()
        self.failUnless('plone_menu.js' in scriptids)
        self.failUnless('plone_javascript_variables.js' in scriptids)
        self.failUnless('test_rr_1.js' in scriptids)

    def testTraverseToConcatenatedDefaults(self):
        scripts = self.tool.getEvaluatedResources(self.portal)
        for s in scripts:
            try:
                magic = s.getId()
                self.portal.restrictedTraverse('portal_javascripts/%s' % magic)
            except KeyError:
                self.fail()

    def testUserConditionOnMenuScript(self):
        scripts1 = self.tool.getEvaluatedResources(self.portal)
        self.logout()
        scripts2 = self.tool.getEvaluatedResources(self.portal)
        self.failUnless(len(scripts1) > len(scripts2))

    def testCallingOfConcatenatedScripts(self):
        stylesheets = self.tool.getEvaluatedResources(self.portal)
        for s in stylesheets:
            if 'ploneScripts' in s.getId():
                output = self.portal.restrictedTraverse(
                             'portal_javascripts/%s' % s.getId())
                break
        if not output:
            self.fail()
        o = str(output)[:]
        self.failIf('&lt;dtml-call' in o)
        self.failIf('&amp;dtml' in o)
        self.failUnless('portal_url' in o)

class TestZODBTraversal(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('red')")
        self.portal.invokeFactory('Folder', 'subfolder')
        self.portal.subfolder.invokeFactory('File',
                                   id='testsubfolder.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('blue')")

        self.tool.registerScript('testroot.js')
        self.tool.registerScript('subfolder/testsubfolder.js')
        self.setRoles(['Member'])

    def testGetItemTraversal(self):
        self.failUnless(self.tool['testroot.js'])
        self.failUnless(self.tool['subfolder/testsubfolder.js'])

    def testGetItemTraversalContent(self):
        self.failUnless('red' in str(self.tool['testroot.js']))
        self.failUnless('blue' in str(self.tool['subfolder/testsubfolder.js']))
        self.failIf('blue' in str(self.tool['testroot.js']))
        self.failIf('red' in str(self.tool['subfolder/testsubfolder.js']))


    def testRestrictedTraverseContent(self):
        self.failUnless('red' in str(
                        self.portal.restrictedTraverse('portal_javascripts/testroot.js')))
        self.failUnless('blue' in str(
                        self.portal.restrictedTraverse('portal_javascripts/subfolder/testsubfolder.js')))
        self.failIf('blue' in str(
                        self.portal.restrictedTraverse('portal_javascripts/testroot.js')))
        self.failIf('red' in str(
                        self.portal.restrictedTraverse('portal_javascripts/subfolder/testsubfolder.js')))

    def testRestrictedTraverseComposition(self):
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].getId()
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        self.failUnless('red' in content)
        self.failUnless('blue' in content)

    def testContextDependantInlineJS(self):
        self.tool.clearResources()
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Folder', 'folder1')
        self.portal.invokeFactory('Folder', 'folder2')
        self.portal.folder1.invokeFactory('File',
                                   id='context.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('pink')")
        self.portal.folder2.invokeFactory('File',
                                   id='context.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('purple')")
        self.tool.registerScript('context.js', inline=True)
        self.setRoles(['Member'])
        content = getattr(self.portal.folder1, 'renderAllTheScripts')()
        self.failUnless('pink' in content)
        self.failIf('purple' in content)
        content = getattr(self.portal.folder2, 'renderAllTheScripts')()
        self.failUnless('purple' in content)
        self.failIf('pink' in content)

class TestResourcePermissions(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.tool.clearResources()
        self.tool.registerScript('testroot.js', cookable=False)
        self.tool.registerScript('test_rr_1.js')
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('red')")

        script = self.portal.restrictedTraverse('testroot.js')

        script.manage_permission('View',['Manager'], acquire=0)
        script.manage_permission('Access contents information',['Manager'], acquire=0)
        self.setRoles(['Member'])

    def testUnauthorizedGetItem(self):
        try:
            content = str(self.tool['testroot.js'])
        except Unauthorized:
            return

        self.fail()

    def testUnauthorizedTraversal(self):
        try:
            content = str(self.portal.restrictedTraverse('portal_javascripts/testroot.js'))
        except Unauthorized:
            return

        self.fail()

    def testTestUnauthorizedTraversal(self):
        try:
            content = str(self.portal.restrictedTraverse('portal_javascripts/testroot.js'))
        except Unauthorized:
            return

        self.fail()

    def testRaiseUnauthorizedOnPublish(self):
        response = self.publish(self.toolpath + '/testroot.js')
        #Will be 302 if CookieCrumbler is enabled
        self.failUnless(response.getStatus() in [302, 403])

    def testRemovedFromResources(self):
        scripts = self.tool.getEvaluatedResources(self.portal)
        ids = [item.getId() for item in scripts]
        self.failIf('testroot.js' in ids)
        self.failUnless('test_rr_1.js' in ids)

    def testRemovedFromMergedResources(self):
        self.tool.unregisterResource('testroot.js')
        self.tool.registerScript('testroot.js')
        scripts = self.tool.getEvaluatedResources(self.portal)
        magicId = None
        for script in scripts:
            id = script.getId()
            if id.startswith(self.tool.filename_base):
                magicId = id
        self.failUnless(magicId)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        self.failIf('red' in content)
        self.failUnless('not authorized' in content)
        self.failUnless('running' in content)

    def testAuthorizedGetItem(self):
        self.setRoles(['Manager'])
        try:
            content = str(self.tool['testroot.js'])
        except Unauthorized:
            self.fail()

    def testAuthorizedTraversal(self):
        self.setRoles(['Manager'])
        try:
            content = str(self.portal.restrictedTraverse('portal_css/testroot.js'))
        except Unauthorized:
            self.fail()

class TestMergingDisabled(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.req_resources = 3
        self.req_cooked = 2
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.tool.registerScript('testroot.js')
        self.tool.registerScript('test_rr_1.js')
        self.tool.registerScript('simple2.js', cookable=False)
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('green')")
        self.portal.invokeFactory('File',
                                   id='simple2.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('blue')")
        self.setRoles(['Member'])

    def testDefaultStylesheetCookableAttribute(self):
        self.failUnless(self.tool.getResources()[self.tool.getResourcePosition('test_rr_1.js')].getCookable())
        self.failUnless(self.tool.getResources()[self.tool.getResourcePosition('testroot.js')].getCookable())

    def testStylesheetCookableAttribute(self):
        self.failIf(self.tool.getResources()[self.tool.getResourcePosition('simple2.js')].getCookable())

    def testNumberOfResources(self):
        req_resources = 3
        req_cooked = 2
        self.assertEqual(len(self.tool.getResources()), req_resources)
        self.assertEqual(len(self.tool.cookedresources), req_cooked)
        self.assertEqual(len(self.tool.concatenatedresources), req_resources + (req_resources - req_cooked ))
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), req_cooked)

    def testCompositionWithLastUncooked(self):
        req_resources = 3
        req_cooked = 2
        self.tool.moveResourceToBottom('simple2.js')
        self.assertEqual(len(self.tool.getResources()), req_resources)
        self.assertEqual(len(self.tool.cookedresources), req_cooked)
        self.assertEqual(len(self.tool.concatenatedresources), req_resources + (req_resources - req_cooked ))
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), req_cooked)
        magicId = None
        for script in scripts:
            id = script.getId()
            if id.startswith(self.tool.filename_base):
                magicId = id
        self.failUnless(magicId)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        self.failUnless('running' in content)
        self.failUnless('green' in content)
        self.failIf('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/simple2.js'))
        self.failUnless('blue' in content)

    def testCompositionWithFirstUncooked(self):
        req_resources = 3
        req_cooked = 2
        self.tool.moveResourceToTop('simple2.js')
        self.assertEqual(len(self.tool.getResources()), req_resources)
        self.assertEqual(len(self.tool.cookedresources), req_cooked)
        self.assertEqual(len(self.tool.concatenatedresources), req_resources + (req_resources - req_cooked ))
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), req_cooked)
        magicId = None
        for script in scripts:
            id = script.getId()
            if id.startswith(self.tool.filename_base):
                magicId = id
        self.failUnless(magicId)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        self.failUnless('running' in content)
        self.failUnless('green' in content)
        self.failIf('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/simple2.js'))
        self.failUnless('blue' in content)

    def testCompositionWithMiddleUncooked(self):
        req_resources = 3
        req_cooked = 3
        self.tool.moveResourceToTop('simple2.js')
        self.tool.moveResourceDown('simple2.js')
        self.assertEqual(len(self.tool.getResources()), req_resources)
        self.assertEqual(len(self.tool.cookedresources), req_cooked)
        self.assertEqual(len(self.tool.concatenatedresources), req_resources + (req_resources - req_cooked ))
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), req_cooked)
        content = str(self.portal.restrictedTraverse('portal_javascripts/simple2.js'))
        self.failUnless('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/test_rr_1.js'))
        self.failUnless('running' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/testroot.js'))
        self.failUnless('green' in content)

    def testLargerCompositionWithMiddleUncooked(self):
        req_cooked = 3
        req_resources = 5
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testpurple.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('purple')")
        self.portal.invokeFactory('File',
                                   id='testpink.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript',
                                   file="window.alert('pink')")
        self.setRoles(['Member'])
        self.tool.registerScript('testpurple.js')
        self.tool.registerScript('testpink.js')
        self.tool.moveResourceToTop('simple2.js')
        self.tool.moveResourceDown('simple2.js', 2)
        #Now have [[green,running],blue,[purple,pink]]
        self.assertEqual(len(self.tool.getResources()), req_resources)
        self.assertEqual(len(self.tool.cookedresources), req_cooked)
        self.assertEqual(len(self.tool.concatenatedresources), req_resources + (req_resources - req_cooked ))
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), req_cooked)
        magicIds = []
        for script in scripts:
            id = script.getId()
            if id.startswith(self.tool.filename_base):
                magicIds.append(id)
        self.assertEqual(len(magicIds), 2)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicIds[0]))
        self.failUnless('running' in content)
        self.failUnless('green' in content)
        self.failIf('pink' in content)
        self.failIf('purple' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicIds[1]))
        self.failUnless('pink' in content)
        self.failUnless('purple' in content)
        self.failIf('running' in content)
        self.failIf('green' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/simple2.js'))
        self.failUnless('blue' in content)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestJSImplementation))
    suite.addTest(makeSuite(TestJSTool))
    suite.addTest(makeSuite(TestJSSkin))
    suite.addTest(makeSuite(testJSZMIMethods))
    suite.addTest(makeSuite(TestJSScriptRegistration))
    suite.addTest(makeSuite(TestJSScriptRenaming))
    suite.addTest(makeSuite(TestJSToolSecurity))
    suite.addTest(makeSuite(TestJSToolExpression))
    suite.addTest(makeSuite(TestJSScriptCooking))
    suite.addTest(makeSuite(TestScriptMoving))
    suite.addTest(makeSuite(TestJSTraversal))
    suite.addTest(makeSuite(TestPublishing))
    suite.addTest(makeSuite(TestDebugMode))
    suite.addTest(makeSuite(TestZODBTraversal))
    suite.addTest(makeSuite(TestMergingDisabled))
    suite.addTest(makeSuite(TestResourcePermissions))

    if not PLONE21:
        # We must not test for the defaults in Plone 2.1 because they are
        # all different. Plone2.1 has tests in CMFPlone/tests for defaults
        # and migrations
        suite.addTest(makeSuite(TestJSDefaults))


    return suite

if __name__ == '__main__':
    framework()
