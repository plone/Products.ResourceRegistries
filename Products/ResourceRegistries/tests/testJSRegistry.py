#
# JSRegistry Tests
#
from zope.component import getMultiAdapter
from zope.contentprovider.interfaces import IContentProvider

from OFS.Image import Pdata
from DateTime import DateTime
from AccessControl import Unauthorized
from zope.interface.verify import verifyObject

from Products.CMFCore.Expression import Expression
from Products.CMFCore.utils import getToolByName

from Products.PloneTestCase.PloneTestCase import portal_owner, default_password

from Products.ResourceRegistries.config import JSTOOLNAME
from Products.ResourceRegistries.interfaces import IJSRegistry
from Products.ResourceRegistries.interfaces import ICookedFile
from Products.ResourceRegistries.tests.RegistryTestCase import RegistryTestCase
from Products.ResourceRegistries.tests.RegistryTestCase import FunctionalRegistryTestCase

class TestJSImplementation(RegistryTestCase):

    def test_interfaces(self):
        tool = getattr(self.portal, JSTOOLNAME)
        self.assertTrue(IJSRegistry.providedBy(tool))
        self.assertTrue(verifyObject(IJSRegistry, tool))


class TestJSTool(RegistryTestCase):

    def testToolExists(self):
        self.assertTrue(JSTOOLNAME in self.portal.objectIds())

    def testZMIForm(self):
        tool = getattr(self.portal, JSTOOLNAME)
        self.setRoles(['Manager'])
        self.assertTrue(tool.manage_jsForm())
        self.assertTrue(tool.manage_jsComposition())


class TestJSSkin(RegistryTestCase):

    def testSkins(self):
        skins = self.portal.portal_skins.objectIds()
        self.assertTrue('ResourceRegistries' in skins)

    def testSkinExists(self):
        self.assertTrue(getattr(self.portal, 'test_rr_1.js'))


class testJSZMIMethods(RegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testAdd(self):
        self.tool.manage_addScript(id='joe')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.assertTrue(self.tool.getResources())


class TestJSScriptRegistration(RegistryTestCase):

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


class TestJSScriptRenaming(RegistryTestCase):

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

    def testRenamingExternal(self):
        old = '//example.org/foo.js'
        new = '//example.org/bar.js'
        self.tool.registerScript(old)
        self.tool.renameResource(old, new)
        self.assertFalse(old in self.tool.getResourceIds())
        self.assertTrue(new in self.tool.getResourceIds())

    def testDoubleRenaming(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.registerScript('eggs')
        self.tool.renameResource('spam', 'bacon')
        self.assertRaises(ValueError, self.tool.renameResource, 'spam', 'bacon')


class TestJSToolSecurity(RegistryTestCase):

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


class TestJSToolExpression(RegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()

    def testSimplestExpression(self):
        context = self.portal
        self.assertTrue(self.tool.evaluateExpression(
            Expression('python:1'), context))
        self.assertFalse(self.tool.evaluateExpression(
            Expression('python:0'), context))
        self.assertTrue(self.tool.evaluateExpression(
            Expression('python:0+1'), context))

    def testNormalExpression(self):
        context = self.portal
        self.assertTrue(self.tool.evaluateExpression(
            Expression('object/absolute_url'), context))

    def testExpressionInFolder(self):
        self.folder.invokeFactory('Document', 'eggs')
        context = self.folder
        self.assertTrue(self.tool.evaluateExpression(
            Expression('python:"eggs" in object.objectIds()'), context))


class TestJSScriptCooking(RegistryTestCase):

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
        magic_ids = [item.getId() for item in self.tool.getEvaluatedResources(self.folder)]
        self.assertTrue('ham' in self.tool.concatenatedresources[magic_ids[0]])
        self.assertTrue('eggs' in self.tool.concatenatedresources[magic_ids[2]])
        self.assertTrue('spam' in self.tool.concatenatedresources[magic_ids[1]])
        self.assertTrue('spam spam' in self.tool.concatenatedresources[magic_ids[1]])
        self.assertTrue('spam spam spam' in self.tool.concatenatedresources[magic_ids[1]])

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
        magic_ids = [item.getId() for item in evaluated]
        ids = []
        for magic_id in magic_ids:
            self.assertEqual(len(self.tool.concatenatedresources[magic_id]), 1)
            ids.append(self.tool.concatenatedresources[magic_id][0])
        self.assertTrue(ids[0] == 'ham')
        self.assertTrue(ids[1] == 'spam')

    def testRenderingScriptLinks(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('ham2merge')
        self.tool.registerScript('spam', expression='string:spam')
        self.tool.registerScript('test_rr_1.css', inline='1')
        view = self.portal.restrictedTraverse('@@plone')
        viewletmanager = getMultiAdapter((self.portal, self.portal.REQUEST, view), IContentProvider, name = u'plone.resourceregistries.scripts')
        viewletmanager.update()
        all = viewletmanager.render()
        evaluated = self.tool.getEvaluatedResources(self.folder)
        magic_ids = [item.getId() for item in evaluated]
        self.assertTrue('background-color' in all)
        self.assertTrue('<script' in all)
        self.assertTrue('/%s' %(magic_ids[1],) in all)

    def testReenderingConcatenatesInline(self):
        self.tool.registerScript('test_rr_1.css', inline='1')
        self.tool.registerScript('test_rr_2.css', inline='1')
        view = self.portal.restrictedTraverse('@@plone')
        viewletmanager = getMultiAdapter((self.portal, self.portal.REQUEST, view), IContentProvider, name = u'plone.resourceregistries.scripts')
        viewletmanager.update()
        all = viewletmanager.render()
        self.assertTrue('background-color' in all)
        self.assertTrue('blue' in all)

    def testRenderingWorksInMainTemplate(self):
        renderedpage = getattr(self.portal, 'index_html')()
        self.assertFalse('background-color' in renderedpage)
        self.tool.registerScript('test_rr_1.css', inline=1)
        renderedpage = getattr(self.portal, 'index_html')()
        self.assertTrue('background-color' in renderedpage)


class TestScriptMoving(RegistryTestCase):

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
        self.tool.moveResourceUp('foo')

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

class TestJSTraversal(RegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.tool.registerScript('test_rr_1.js')

    def testMarker(self):
        traversed = self.portal.restrictedTraverse('portal_javascripts/test_rr_1.js')
        self.assertTrue(ICookedFile.providedBy(traversed))
    
    def testMarkerComposite(self):
        self.tool.registerScript('test_rr_2.css')
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].getId()
        traversed = self.portal.restrictedTraverse('portal_javascripts/%s' % magicId)
        self.assertTrue(ICookedFile.providedBy(traversed))

    def testGetItemTraversal(self):
        self.assertTrue(self.tool['test_rr_1.js'])

    def testGetItemTraversalContent(self):
        self.assertTrue('running' in str(
                        self.tool['test_rr_1.js']))

    def testRestrictedTraverseContent(self):
        self.assertTrue('running' in str(
                        self.portal.restrictedTraverse(
                            'portal_javascripts/test_rr_1.js')))

    def testRestrictedTraverseComposition(self):
        self.tool.registerScript('test_rr_2.css')
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].getId()
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        # XXX: Review
        #self.assertTrue('test_rr_1.js' in content)
        #self.assertTrue('registerPloneFunction' in content)

    def testCompositesWithBrokenId(self):
        self.tool.registerScript('nonexistant.js')
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].getId()
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))


class TestPublishing(FunctionalRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.folderpath = '/' + self.folder.absolute_url(1)
        self.tool.registerScript('test_rr_1.js')
        self.folder.invokeFactory('Document', 'index_html')
        self.setRoles(['Manager'])
        self.workflow = self.portal.portal_workflow
        self.workflow.doActionFor(self.folder, 'publish')
        self.workflow.doActionFor(self.folder.index_html, 'publish')
        self.setRoles(['Member'])

    def testPublishJSThroughTool(self):
        response = self.publish(self.toolpath + '/test_rr_1.js')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'), 'application/x-javascript;charset=utf-8')

    def testPublishNonMagicJSThroughTool(self):
        self.setRoles(['Manager'])
        body = """<dtml-var "'joined' + 'string'">"""
        self.folder.addDTMLMethod('testmethod', file=body)
        self.tool.registerScript('testmethod')
        response = self.publish(self.toolpath + '/testmethod')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'), 'application/x-javascript;charset=utf-8')

    def testPublishPageWithInlineJS(self):
        # This one fails from string/utf-8 concatenation
        response = self.publish(self.folderpath)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.tool.clearResources()
        self.tool.registerScript('test_rr_1.js', inline=True)
        # Test that the main page retains its content-type
        response = self.publish(self.folderpath)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.assertEqual(response.getStatus(), 200)

    def testPublishPageWithInlineJS2(self):
        self.tool.clearResources()
        # Test that the main page retains its content-type
        self.setRoles(['Manager'])
        body = """<dtml-call "REQUEST.RESPONSE.setHeader('Content-Type', 'text/javascript')">/*and some js comments too*/ """
        self.folder.addDTMLMethod('testmethod', file=body)
        self.tool.registerScript('testmethod', inline=True)
        response = self.publish(self.folderpath)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.assertEqual(response.getStatus(), 200)

class TestRequestTypesInlineRendering(FunctionalRegistryTestCase):
    # Test how well various request types render resources inline.
    # See http://dev.plone.org/ticket/8998

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        # Define an inline resource
        self.tool.registerScript('++resource++test_rr_1.js', inline=True)
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)

    def testGETRequest(self):
        response = self.publish(self.portalpath, request_method='GET')
        self.assertEqual(response.getStatus(), 200)
        self.assertTrue("window.alert('running')" in response.getBody())

    def testHEADRequest(self):
        response = self.publish(self.portalpath, request_method='HEAD')
        self.assertEqual(response.getStatus(), 200)
        # This is a HEAD request, so we won't get anything back.
        self.assertTrue(response.getBody() == '')

    def testPOSTRequest(self):
        response = self.publish(self.portalpath, request_method='POST')
        self.assertEqual(response.getStatus(), 200)
        self.assertTrue("window.alert('running')" in response.getBody())

class TestFivePublishing(FunctionalRegistryTestCase):
    'Publishing with Five'

    def afterSetUp(self):
        # Define some resource
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.tool.registerScript('++resource++test_rr_1.js')
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'index_html')
        self.setRoles(['Member'])

    def testPublishFiveResource(self):
        response = self.publish(self.toolpath + '/++resource++test_rr_1.js')
        self.assertEqual(response.getStatus(), 200)
        self.assertTrue(response.getHeader('Content-Type').endswith('javascript'))
        self.assertEqual("window.alert('running')" in response.getBody(), True)

class TestDebugMode(FunctionalRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)
        self.toolpath = '/' + self.tool.absolute_url(1)

    def testDebugModeSplitting(self):
        self.tool.registerScript('ham')
        self.tool.registerScript('spam')
        self.tool.setDebugMode(False)
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)
        self.tool.setDebugMode(True)
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 2)

    def testDebugModeSplitting2(self):
        self.tool.registerScript('ham')
        # Publish in normal mode
        response = self.publish(self.toolpath+'/ham')
        now = DateTime()
        days = 7
        soon = now + days
        self.tool.setDebugMode(True)
        # Publish in debug mode
        response = self.publish(self.toolpath+'/ham')
        self.assertExpiresNotEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertExpiresEqual(response.getHeader('Expires'), now.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=0')


class TestZODBTraversal(RegistryTestCase):

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
        self.tool.setDebugMode(False)

    def testGetItemTraversal(self):
        self.assertTrue(self.tool['testroot.js'])
        self.assertTrue(self.tool['subfolder/testsubfolder.js'])

    def testGetItemTraversalContent(self):
        self.assertTrue('red' in str(self.tool['testroot.js']))
        self.assertTrue('blue' in str(self.tool['subfolder/testsubfolder.js']))
        self.assertFalse('blue' in str(self.tool['testroot.js']))
        self.assertFalse('red' in str(self.tool['subfolder/testsubfolder.js']))


    def testRestrictedTraverseContent(self):
        self.assertTrue('red' in str(
                        self.portal.restrictedTraverse('portal_javascripts/testroot.js')))
        self.assertTrue('blue' in str(
                        self.portal.restrictedTraverse('portal_javascripts/subfolder/testsubfolder.js')))
        self.assertFalse('blue' in str(
                        self.portal.restrictedTraverse('portal_javascripts/testroot.js')))
        self.assertFalse('red' in str(
                        self.portal.restrictedTraverse('portal_javascripts/subfolder/testsubfolder.js')))

    def testRestrictedTraverseComposition(self):
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].getId()
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        self.assertTrue('red' in content)
        self.assertTrue('blue' in content)

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
        view = self.portal.restrictedTraverse('@@plone')
        viewletmanager = getMultiAdapter((self.portal.folder1, self.portal.folder1.REQUEST, view), IContentProvider, name = u'plone.resourceregistries.scripts')
        viewletmanager.update()
        content = viewletmanager.render()
        self.assertTrue('pink' in content)
        self.assertFalse('purple' in content)
        view = self.portal.restrictedTraverse('@@plone')
        viewletmanager = getMultiAdapter((self.portal.folder2, self.portal.folder2.REQUEST, view), IContentProvider, name = u'plone.resourceregistries.scripts')
        viewletmanager.update()
        content = viewletmanager.render()
        self.assertTrue('purple' in content)
        self.assertFalse('pink' in content)

class TestResourcePermissions(FunctionalRegistryTestCase):

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
        self.tool.setDebugMode(False)

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
        self.assertTrue(response.getStatus() in [302, 403, 401])

    def testRemovedFromResources(self):
        # This test assumes that content is not merged or cached
        self.tool.unregisterResource('test_rr_1.js')
        self.tool.registerResource('test_rr_1.js', cookable=False, cacheable=False)
        scripts = self.tool.getEvaluatedResources(self.portal)
        ids = [item.getId() for item in scripts]
        self.assertFalse('testroot.js' in ids)
        self.assertTrue('test_rr_1.js' in ids)
        # Return resources to normal (not sure if this is needed)
        self.tool.unregisterResource('test_rr_1.js')
        self.tool.registerScript('test_rr_1.js')

    def testRemovedFromMergedResources(self):
        self.tool.unregisterResource('testroot.js')
        self.tool.registerScript('testroot.js')
        scripts = self.tool.getEvaluatedResources(self.portal)
        magicId = None
        for script in scripts:
            id = script.getId()
            if '-cachekey' in id:
                magicId = id
        self.assertTrue(magicId)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        self.assertFalse('red' in content)
        self.assertTrue('not authorized' in content)
        self.assertTrue('running' in content)

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

    def testAuthorizedOnPublish(self):
        authstr = "%s:%s" % (portal_owner, default_password)
        response = self.publish(self.toolpath + '/testroot.js', basic=authstr)
        self.assertEqual(response.getStatus(), 200)

class TestMergingDisabled(RegistryTestCase):

    def afterSetUp(self):
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
        self.tool.setDebugMode(False)

    def testDefaultStylesheetCookableAttribute(self):
        self.assertTrue(self.tool.getResources()[self.tool.getResourcePosition('test_rr_1.js')].getCookable())
        self.assertTrue(self.tool.getResources()[self.tool.getResourcePosition('testroot.js')].getCookable())

    def testStylesheetCookableAttribute(self):
        self.assertFalse(self.tool.getResources()[self.tool.getResourcePosition('simple2.js')].getCookable())

    def testNumberOfResources(self):
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 5)
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 2)

    def testCompositionWithLastUncooked(self):
        self.tool.moveResourceToBottom('simple2.js')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 5)
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 2)
        magicIds = []
        for script in scripts:
            id = script.getId()
            if '-cachekey' in id:
                magicIds.append(id)
        self.assertTrue(magicIds[-1].startswith('simple2'))
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicIds[-2]))
        self.assertTrue('running' in content)
        self.assertTrue('green' in content)
        self.assertFalse('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicIds[-1]))
        self.assertFalse('running' in content)
        self.assertFalse('green' in content)
        self.assertTrue('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/simple2.js'))
        self.assertTrue('blue' in content)

    def testCompositionWithFirstUncooked(self):
        self.tool.moveResourceToTop('simple2.js')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 5)
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 2)
        magicId = None
        for script in scripts:
            id = script.getId()
            if '-cachekey' in id:
                magicId = id
        self.assertTrue(magicId)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicId))
        self.assertTrue('running' in content)
        self.assertTrue('green' in content)
        self.assertFalse('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/simple2.js'))
        self.assertTrue('blue' in content)

    def testCompositionWithMiddleUncooked(self):
        self.tool.moveResourceToTop('simple2.js')
        self.tool.moveResourceDown('simple2.js')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 3)
        self.assertEqual(len(self.tool.concatenatedresources), 6)
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 3)
        content = str(self.portal.restrictedTraverse('portal_javascripts/simple2.js'))
        self.assertTrue('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/test_rr_1.js'))
        self.assertTrue('running' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/testroot.js'))
        self.assertTrue('green' in content)

    def testLargerCompositionWithMiddleUncooked(self):
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
        self.assertEqual(len(self.tool.getResources()), 5)
        self.assertEqual(len(self.tool.cookedresources), 3)
        self.assertEqual(len(self.tool.concatenatedresources), 8)
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 3)
        magicIds = []
        for script in scripts:
            id = script.getId()
            if '-cachekey' in id:
                magicIds.append(id)
        self.assertEqual(len(magicIds), 3)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicIds[0]))
        self.assertTrue('running' in content)
        self.assertTrue('green' in content)
        self.assertFalse('pink' in content)
        self.assertFalse('purple' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/%s' % magicIds[2]))
        self.assertTrue('pink' in content)
        self.assertTrue('purple' in content)
        self.assertFalse('running' in content)
        self.assertFalse('green' in content)
        content = str(self.portal.restrictedTraverse('portal_javascripts/simple2.js'))
        self.assertTrue('blue' in content)


class TestUnicodeAwareness(RegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        body = "/* add a comment with unicode\n   \xc3\x9bercool! */\nwindow.alert('running')\n"
        self.setRoles(['Manager'])
        self.portal.addDTMLMethod('testmethod.js', file=body)
        self.portal.invokeFactory('File',
                                   id='testfile.js',
                                   format='application/x-javascript',
                                   content_type='application/x-javascript;charset=utf-8',
                                   file=body)
        self.setRoles(['Member'])
        self.tool.setDebugMode(False)

    def testGetOriginal(self):
        # this needs to be first because it's a zpt returning unicode
        self.tool.registerScript('test_rr_1.js')
        self.tool.registerScript('++resource++test_rr_1.js')
        self.tool.registerScript('test_rr_2.js')
        self.tool.registerScript('test_rr_3.js')
        self.tool.registerScript('testmethod.js')
        self.tool.registerScript('testfile.js')
        self.tool.registerScript('@@streamed-resource')
        scripts = self.tool.getEvaluatedResources(self.portal)
        magicId = None
        for script in scripts:
            id = script.getId()
            if '-cachekey' in id:
                magicId = id
        self.assertTrue(magicId)
        content = self.tool.getResourceContent(magicId, self.portal, original=True)

        self.assertTrue(u"window.alert('running')" in content)
        self.assertTrue(u"alert('streamed');" in content)

class TestCachingHeaders(FunctionalRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.skins_tool = getToolByName(self.portal, 'portal_skins')
        self.tool.clearResources()
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.tool.setDebugMode(False)

    def testCachingHeadersFromTool(self):
        self.tool.registerScript('ham')
        # Publish
        response = self.publish(self.toolpath+'/ham')
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertExpiresEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

        # Publish again
        response = self.publish(self.toolpath+'/ham')
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertExpiresEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

    def testCachingHeadersFromSkin(self):
        self.tool.registerScript('ham')
        # Publish in normal mode
        skinpath = self.skins_tool.getDefaultSkin()
        url = '%s/%s/ham' % (self.toolpath, skinpath)
        response = self.publish(url)
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertExpiresEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

        # Publish again
        response = self.publish(url)
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertExpiresEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

    def testCachingHeadersFromToolWithRAMCache(self):
        ram_cache_id = 'RAMCache'
        self.tool.ZCacheable_setManagerId(ram_cache_id)
        self.tool.ZCacheable_setEnabled(1)
        self.tool.registerScript('ham')
        # Publish
        response = self.publish(self.toolpath+'/ham')
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertExpiresEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

        # Publish again
        response = self.publish(self.toolpath+'/ham')
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertExpiresEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

    def testCachingHeadersFromSkinWithRAMCache(self):
        ram_cache_id = 'RAMCache'
        self.tool.ZCacheable_setManagerId(ram_cache_id)
        self.tool.ZCacheable_setEnabled(1)
        self.tool.registerScript('ham')
        # Publish in normal mode
        skinpath = self.skins_tool.getDefaultSkin()
        url = '%s/%s/ham' % (self.toolpath, skinpath)
        response = self.publish(url)
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertExpiresEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

        # Publish again
        response = self.publish(url)
        now = DateTime()
        days = 7
        soon = now + days
        self.assertEqual(response.getStatus(), 200)
        self.assertExpiresEqual(response.getHeader('Expires'), soon.timeTime())
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=%d' % int(days*24*3600))

class TestBundling(RegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        
        # Fake install of portal_registry tool
        from Products.ResourceRegistries.interfaces.settings import IResourceRegistriesSettings
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility
        
        self.portal['portal_skins'].addSkinSelection('alpha', 'pink,ResourceRegistries')
        self.portal['portal_skins'].addSkinSelection('beta', 'purple,ResourceRegistries')
        self.portal['portal_skins'].addSkinSelection('delta', 'yellow,ResourceRegistries')
        
        self.registry = getUtility(IRegistry)
        self.registry.registerInterface(IResourceRegistriesSettings)

    def test_getBundlesForThemes_default(self):
        bundlesForThemes = self.tool.getBundlesForThemes()
        for theme in self.portal['portal_skins'].getSkinSelections():
            self.assertTrue('default' in bundlesForThemes[theme])
            self.assertTrue('default' in self.tool.getBundlesForTheme(theme))
    
    def test_getBundlesForTheme_fallback(self):
        self.assertEqual(self.tool.getBundlesForTheme('invalid-theme'), ['default'])

    def test_manage_saveBundlesForThemes(self):
        self.tool.manage_saveBundlesForThemes({
                'alpha': ['default', 'foobar'],
                'beta': [],
            })
        
        self.assertEqual(self.tool.getBundlesForTheme('alpha'), ['default', 'foobar'])
        self.assertEqual(self.tool.getBundlesForTheme('beta'), [])
        self.assertEqual(self.tool.getBundlesForTheme('invalid-theme'), ['default'])

    def test_getCookedResourcesByTheme(self):
        self.tool.registerScript('ham', bundle='default')
        self.tool.registerScript('spam', bundle='foo')
        self.tool.registerScript('eggs') # will be in the 'default' bundle
        
        self.tool.manage_saveBundlesForThemes({
                'alpha': ['default', 'foo'],
                'beta': ['foo'],
                'delta': ['default'],
            })
        
        merged = self.tool.getCookedResources('alpha')
        self.assertEqual(len(merged), 1)
        components = self.tool.concatenatedResourcesByTheme['alpha'][merged[0].getId()]
        self.assertEqual(components, ['ham', 'spam', 'eggs'])
        
        merged = self.tool.getCookedResources('beta')
        self.assertEqual(len(merged), 1)
        components = self.tool.concatenatedResourcesByTheme['beta'][merged[0].getId()]
        self.assertEqual(components, ['spam'])
        
        merged = self.tool.getCookedResources('delta')
        self.assertEqual(len(merged), 1)
        components = self.tool.concatenatedResourcesByTheme['delta'][merged[0].getId()]
        self.assertEqual(components, ['ham', 'eggs'])
        
        current = self.portal['portal_skins'].getCurrentSkinName()
        merged = self.tool.getCookedResources(current)
        self.assertEqual(len(merged), 1)
        components = self.tool.concatenatedResourcesByTheme[current][merged[0].getId()]
        self.assertEqual(components, ['ham', 'eggs'])

class TestPdataAwareness(FunctionalRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, JSTOOLNAME)
        self.tool.clearResources()
        self.toolpath = '/' + self.tool.absolute_url(1)

        self.setRoles(['Manager'])
        self.skinstool = getattr(self.portal, 'portal_skins')
        self.skinstool.custom.manage_addFile(id='hello_world.js',
                                   content_type='application/javascript',
                                   file=Pdata('alert("Hello world!");'))
        self.tool.registerScript('hello_world.js')
        self.setRoles(['Member'])

    def testPublishFileResourceWithPdata(self):
        default_skin_name = self.skinstool.getDefaultSkin()
        response = self.publish(self.toolpath + '/' + default_skin_name +\
                                '/hello_world.js')
        self.assertEqual(response.getStatus(), 200)
        self.assertTrue('Hello world!' in str(response))


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
    suite.addTest(makeSuite(TestRequestTypesInlineRendering))
    suite.addTest(makeSuite(TestFivePublishing))
    suite.addTest(makeSuite(TestDebugMode))
    suite.addTest(makeSuite(TestZODBTraversal))
    suite.addTest(makeSuite(TestMergingDisabled))
    suite.addTest(makeSuite(TestResourcePermissions))
    suite.addTest(makeSuite(TestUnicodeAwareness))
    suite.addTest(makeSuite(TestCachingHeaders))
    suite.addTest(makeSuite(TestBundling))
    suite.addTest(makeSuite(TestPdataAwareness))
    return suite
