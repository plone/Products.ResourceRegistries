#
# CSSRegistry Tests
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

from Products.ResourceRegistries.config import CSSTOOLNAME
from Products.ResourceRegistries.interfaces import ICSSRegistry
from Products.ResourceRegistries.tests import CSSRegistryTestCase


class TestImplementation(CSSRegistryTestCase.CSSRegistryTestCase):

    def test_interfaces(self):
        tool = getattr(self.portal, CSSTOOLNAME)
        self.failUnless(ICSSRegistry.isImplementedBy(tool))
        self.failUnless(verifyObject(ICSSRegistry, tool))


class TestTool(CSSRegistryTestCase.CSSRegistryTestCase):

    def testToolExists(self):
        self.failUnless(CSSTOOLNAME in self.portal.objectIds())

    def testZMIForm(self):
        tool = getattr(self.portal, CSSTOOLNAME)
        self.setRoles(['Manager'])
        self.failUnless(tool.manage_cssForm())
        self.failUnless(tool.manage_cssComposition())


class TestSkin(CSSRegistryTestCase.CSSRegistryTestCase):

    def testSkins(self):
        skins = self.portal.portal_skins.objectIds()
        self.failUnless('ResourceRegistries' in skins)

    def testSkinExists(self):
        self.failUnless(getattr(self.portal, 'renderAllTheStylesheets'))


class testZMIMethods(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()

    def testAdd(self):
        self.tool.manage_addStylesheet(id='joe')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.failUnless(self.tool.getResources())


class TestStylesheetRegistration(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()

    def testStoringStylesheet(self):
        self.tool.registerStylesheet('foo')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.assertEqual(self.tool.getResources()[0].getId(), 'foo')

    def testDefaultStylesheetAttributes(self):
        self.tool.registerStylesheet('foodefault')
        self.assertEqual(self.tool.getResources()[0].getId(), 'foodefault')
        self.assertEqual(self.tool.getResources()[0].getExpression(), '')
        self.assertEqual(self.tool.getResources()[0].getMedia(), None)
        self.assertEqual(self.tool.getResources()[0].getRel(), 'stylesheet')
        self.assertEqual(self.tool.getResources()[0].getTitle(), None)
        self.assertEqual(self.tool.getResources()[0].getRendering(), 'import')
        self.failUnless(self.tool.getResources()[0].getEnabled())

    def testStylesheetAttributes(self):
        self.tool.registerStylesheet('foo', expression='python:1',
                                     media='print', rel='alternate stylesheet',
                                     title='Foo', rendering='inline', enabled=0)
        self.assertEqual(self.tool.getResources()[0].getId(), 'foo')
        self.assertEqual(self.tool.getResources()[0].getExpression(), 'python:1')
        self.assertEqual(self.tool.getResources()[0].getMedia(), 'print')
        self.assertEqual(self.tool.getResources()[0].getRel(), 'alternate stylesheet')
        self.assertEqual(self.tool.getResources()[0].getTitle(), 'Foo')
        self.assertEqual(self.tool.getResources()[0].getRendering(), 'inline')
        self.failIf(self.tool.getResources()[0].getEnabled())

    def testDisallowingDuplicateIds(self):
        self.tool.registerStylesheet('foo')
        self.assertRaises(ValueError, self.tool.registerStylesheet, 'foo')

    def testPloneCustomStaysOnTop(self):
        self.tool.registerStylesheet('foo')
        self.tool.registerStylesheet('ploneCustom.css')
        self.tool.registerStylesheet('bar')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(self.tool.getResourceIds(),
                         ('foo', 'bar', 'ploneCustom.css'))

    def testUnregisterStylesheet(self):
        self.tool.registerStylesheet('foo')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.assertEqual(self.tool.getResources()[0].getId(), 'foo')
        self.tool.unregisterResource('foo')
        self.assertEqual(len(self.tool.getResources()), 0)

    def testStylesheetsDict(self):
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('ham')
        keys = self.tool.getResourcesDict().keys()
        keys.sort()
        res = ['ham', 'spam']
        res.sort()
        self.assertEqual(res, keys)
        self.assertEqual(self.tool.getResourcesDict()['ham'].getId(), 'ham')


class TestStylesheetRenaming(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()

    def testRenaming(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])
        self.tool.renameResource('spam', 'bacon')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'bacon', 'eggs'])

    def testRenamingIdClash(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertRaises(ValueError, self.tool.renameResource, 'spam', 'eggs')

    def testDoubleRenaming(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.tool.renameResource('spam', 'bacon')
        self.assertRaises(ValueError, self.tool.renameResource, 'spam', 'bacon')


class TestToolSecurity(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()

    def testRegistrationSecurity(self):
        self.assertRaises(Unauthorized, self.tool.restrictedTraverse,
                          'registerStylesheet')
        self.assertRaises(Unauthorized, self.tool.restrictedTraverse,
                          'unregisterResource')
        self.setRoles(['Manager'])
        try:
            self.tool.restrictedTraverse('registerStylesheet')
            self.tool.restrictedTraverse('unregisterResource')
        except Unauthorized:
            self.fail()


class TestToolExpression(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
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


class TestStylesheetCooking(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()

    def testStylesheetCooking(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 1)
        self.assertEqual(len(self.tool.concatenatedresources.keys()), 4)

    def testStylesheetCookingValues(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])

    def testGetEvaluatedStylesheetsCollapsing(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testMoreComplexStylesheetsCollapsing(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam', expression='string:spam')
        self.tool.registerStylesheet('spam spam', expression='string:spam')
        self.tool.registerStylesheet('spam spam spam', expression='string:spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 3)
        magic_ids = [item.getId() for item in self.tool.getEvaluatedResources(self.folder)]
        self.failUnless('ham' in self.tool.concatenatedresources[magic_ids[0]])
        self.failUnless('eggs' in self.tool.concatenatedresources[magic_ids[2]])
        self.failUnless('spam' in self.tool.concatenatedresources[magic_ids[1]])
        self.failUnless('spam spam' in self.tool.concatenatedresources[magic_ids[1]])
        self.failUnless('spam spam spam' in self.tool.concatenatedresources[magic_ids[1]])

    def testConcatenatedStylesheetsHaveNoMedia(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam', media='print')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)
        self.failIf(self.tool.getEvaluatedResources(self.folder)[0].getMedia())

    def testGetEvaluatedStylesheetsWithExpression(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam', expression='python:1')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 2)

    def testGetEvaluatedStylesheetsWithFailingExpression(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam', expression='python:0')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testGetEvaluatedStylesheetsWithContextualExpression(self):
        self.folder.invokeFactory('Document', 'eggs')
        self.tool.registerStylesheet('spam', expression='python:"eggs" in object.objectIds()')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testCollapsingStylesheetsLookup(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam', expression='string:ham')
        self.tool.registerStylesheet('spam spam', expression='string:ham')
        evaluated = self.tool.getEvaluatedResources(self.folder)
        self.assertEqual(len(evaluated), 2)

    def testRenderingIsInTheRightOrder(self):
        self.tool.registerStylesheet('ham', expression='string:ham')
        self.tool.registerStylesheet('spam', expression='string:spam')
        evaluated = self.tool.getEvaluatedResources(self.folder)
        magic_ids = [item.getId() for item in evaluated]
        ids = []
        for magic_id in magic_ids:
            self.assertEqual(len(self.tool.concatenatedresources[magic_id]), 1)
            ids.append(self.tool.concatenatedresources[magic_id][0])
        self.failUnless(ids[0] == 'ham')
        self.failUnless(ids[1] == 'spam')

    def testConcatenatedSheetsAreInTheRightOrderToo(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        evaluated = self.tool.getEvaluatedResources(self.folder)
        results = self.tool.concatenatedresources[evaluated[0].getId()]
        self.failUnless(results[0] == 'ham')
        self.failUnless(results[1] == 'spam')
        self.failUnless(results[2] == 'eggs')

    def testRenderingStylesheetLinks(self):
        self.tool.registerStylesheet('ham', rendering='link')
        self.tool.registerStylesheet('ham 2 b merged', rendering='link')
        self.tool.registerStylesheet('spam', expression='string:ham', rendering='link')
        self.tool.registerStylesheet('test_rr_1.css', rendering='inline')
        all = getattr(self.portal, 'renderAllTheStylesheets')()
        evaluated = self.tool.getEvaluatedResources(self.folder)
        magic_ids = [item.getId() for item in evaluated]
        self.failUnless('background-color' in all)
        self.failUnless('<link' in all)
        self.failUnless('/%s' % magic_ids[1] in all)
        self.failIf('/test_rr_1.css' in all)

    def testReenderingConcatenatesInline(self):
        self.tool.registerStylesheet('test_rr_1.css', rendering='inline')
        self.tool.registerStylesheet('test_rr_2.css', rendering='inline')
        all = getattr(self.portal, 'renderAllTheStylesheets')()
        self.failUnless('background-color' in all)
        self.failUnless('blue' in all)

    def testDifferentMediaAreCollapsed(self):
        self.tool.registerStylesheet('test_rr_1.css', media='print')
        self.tool.registerStylesheet('test_rr_2.css', media='all')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testDifferentRenderingAreNotCollapsed(self):
        self.tool.registerStylesheet('ham', rendering='inline')
        self.tool.registerStylesheet('spam', rendering='link')
        self.tool.registerStylesheet('egg', rendering='inline')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 3)

    def testRenderingWorksInMainTemplate(self):
        renderedpage = getattr(self.portal, 'index_html')()
        self.failIf('background-color' in renderedpage)
        self.tool.registerStylesheet('test_rr_1.css', rendering='inline')
        renderedpage = getattr(self.portal, 'index_html')()
        self.failUnless('background-color' in renderedpage)


class TestStylesheetMoving(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()

    def testStylesheetMoveDown(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceDown('spam')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'eggs', 'spam'))

    def testStylesheetMoveDownAtEnd(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceDown('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))

    def testStylesheetMoveUp(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceUp('spam')
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'ham', 'eggs'))

    def testStylesheetMoveUpAtStart(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceUp('ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))

    def testStylesheetMoveIllegalId(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.assertRaises(NotFound, self.tool.moveResourceUp, 'foo')

    def testStylesheetMoveToBottom(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceToBottom('ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'eggs', 'ham'))

    def testStylesheetMoveToTop(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceToTop('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('eggs', 'ham', 'spam'))

    def testStylesheetMoveBefore(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.tool.registerStylesheet('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResourceBefore('bacon', 'ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('bacon', 'ham', 'spam', 'eggs'))
        self.tool.moveResourceBefore('bacon', 'eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'bacon', 'eggs'))

    def testStylesheetMoveAfter(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.tool.registerStylesheet('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResourceAfter('bacon', 'ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'bacon', 'spam', 'eggs'))
        self.tool.moveResourceAfter('bacon', 'spam')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'bacon', 'eggs'))

    def testStylesheetMove(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.tool.registerStylesheet('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResource('ham', 2)
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'eggs', 'ham', 'bacon'))
        self.tool.moveResource('bacon', 0)
        self.assertEqual(self.tool.getResourceIds(),
                         ('bacon', 'spam', 'eggs', 'ham'))


class TestTraversal(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()
        self.tool.registerStylesheet('test_rr_1.css')

    def testGetItemTraversal(self):
        self.failUnless(self.tool['test_rr_1.css'])

    def testGetItemTraversalContent(self):
        self.failUnless('background-color' in str(self.tool['test_rr_1.css']))

    def testRestrictedTraverseContent(self):
        self.failUnless('background-color' in str(
                        self.portal.restrictedTraverse('portal_css/test_rr_1.css')))

    def testRestrictedTraverseComposition(self):
        self.tool.registerStylesheet('test_rr_2.css')
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 1)
        magicId = styles[0].getId()
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicId))
        self.failUnless('background-color' in content)
        self.failUnless('blue' in content)

    def testCompositesWithBrokedId(self):
        self.tool.registerStylesheet('nonexistant.css')
        stylesheets = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(stylesheets), 1)
        magicId = stylesheets[0].getId()
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicId))

    def testMediadescriptorsInConcatenatedStylesheets(self):
        self.tool.registerStylesheet('test_rr_2.css', media='print')
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 1)
        magicId = styles[0].getId()
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicId))
        self.failUnless('@media print' in content)
        self.failUnless('background-color : red' in content)
        self.failUnless('H1 { color: blue; }' in content)

class TestZODBTraversal(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.css',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : red }')
        self.portal.invokeFactory('Folder', 'subfolder')
        self.portal.subfolder.invokeFactory('File',
                                   id='testsubfolder.css',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : blue }')

        self.tool.registerStylesheet('testroot.css')
        self.tool.registerStylesheet('subfolder/testsubfolder.css')
        self.setRoles(['Member'])

    def testGetItemTraversal(self):
        self.failUnless(self.tool['testroot.css'])
        self.failUnless(self.tool['subfolder/testsubfolder.css'])

    def testGetItemTraversalContent(self):
        self.failUnless('red' in str(self.tool['testroot.css']))
        self.failUnless('blue' in str(self.tool['subfolder/testsubfolder.css']))
        self.failIf('blue' in str(self.tool['testroot.css']))
        self.failIf('red' in str(self.tool['subfolder/testsubfolder.css']))


    def testRestrictedTraverseContent(self):
        self.failUnless('red' in str(
                        self.portal.restrictedTraverse('portal_css/testroot.css')))
        self.failUnless('blue' in str(
                        self.portal.restrictedTraverse('portal_css/subfolder/testsubfolder.css')))
        self.failIf('blue' in str(
                        self.portal.restrictedTraverse('portal_css/testroot.css')))
        self.failIf('red' in str(
                        self.portal.restrictedTraverse('portal_css/subfolder/testsubfolder.css')))

    def testRestrictedTraverseComposition(self):
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 1)
        magicId = styles[0].getId()
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicId))
        self.failUnless('background-color' in content)
        self.failUnless('red' in content)
        self.failUnless('blue' in content)

    def testContextDependantInlineCSS(self):
        self.tool.clearResources()
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Folder', 'folder1')
        self.portal.invokeFactory('Folder', 'folder2')
        self.portal.folder1.invokeFactory('File',
                                   id='context.css',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : pink }')
        self.portal.folder2.invokeFactory('File',
                                   id='context.css',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : purple }')
        self.tool.registerStylesheet('context.css', rendering='inline')
        self.setRoles(['Member'])
        content = getattr(self.portal.folder1, 'renderAllTheStylesheets')()
        self.failUnless('pink' in content)
        self.failIf('purple' in content)
        content = getattr(self.portal.folder2, 'renderAllTheStylesheets')()
        self.failUnless('purple' in content)
        self.failIf('pink' in content)

class TestMergingDisabled(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()
        self.tool.registerStylesheet('testroot.css')
        self.tool.registerStylesheet('test_rr_1.css')
        self.tool.registerStylesheet('test_rr_2.css', cookable=False)
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.css',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : green }')
        self.setRoles(['Member'])

    def testDefaultStylesheetCookableAttribute(self):
        self.failUnless(self.tool.getResources()[self.tool.getResourcePosition('test_rr_1.css')].getCookable())
        self.failUnless(self.tool.getResources()[self.tool.getResourcePosition('testroot.css')].getCookable())

    def testStylesheetCookableAttribute(self):
        self.failIf(self.tool.getResources()[self.tool.getResourcePosition('test_rr_2.css')].getCookable())

    def testNumberOfResources(self):
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 4)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 2)

    def testCompositionWithLastUncooked(self):
        self.tool.moveResourceToBottom('test_rr_2.css')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 4)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 2)
        magicId = None
        for style in styles:
            id = style.getId()
            if id.startswith(self.tool.filename_base):
                magicId = id
        self.failUnless(magicId)
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicId))
        self.failUnless('red' in content)
        self.failUnless('green' in content)
        self.failIf('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_css/test_rr_2.css'))
        self.failUnless('blue' in content)

    def testCompositionWithFirstUncooked(self):
        self.tool.moveResourceToTop('test_rr_2.css')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 4)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 2)
        magicId = None
        for style in styles:
            id = style.getId()
            if id.startswith(self.tool.filename_base):
                magicId = id
        self.failUnless(magicId)
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicId))
        self.failUnless('red' in content)
        self.failUnless('green' in content)
        self.failIf('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_css/test_rr_2.css'))
        self.failUnless('blue' in content)

    def testCompositionWithMiddleUncooked(self):
        self.tool.moveResourceToTop('test_rr_2.css')
        self.tool.moveResourceDown('test_rr_2.css')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 3)
        self.assertEqual(len(self.tool.concatenatedresources), 5)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 3)
        content = str(self.portal.restrictedTraverse('portal_css/test_rr_2.css'))
        self.failUnless('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_css/test_rr_1.css'))
        self.failUnless('red' in content)
        content = str(self.portal.restrictedTraverse('portal_css/testroot.css'))
        self.failUnless('green' in content)

    def testLargerCompositionWithMiddleUncooked(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testpurple.css',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : purple }')
        self.portal.invokeFactory('File',
                                   id='testpink.css',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : pink }')
        self.setRoles(['Member'])
        self.tool.registerStylesheet('testpurple.css')
        self.tool.registerStylesheet('testpink.css')
        self.tool.moveResourceToTop('test_rr_2.css')
        self.tool.moveResourceDown('test_rr_2.css', 2)
        #Now have [[green,red],blue,[purple,pink]]
        self.assertEqual(len(self.tool.getResources()), 5)
        self.assertEqual(len(self.tool.cookedresources), 3)
        self.assertEqual(len(self.tool.concatenatedresources), 7)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 3)
        magicIds = []
        for style in styles:
            id = style.getId()
            if id.startswith(self.tool.filename_base):
                magicIds.append(id)
        self.assertEqual(len(magicIds), 2)
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicIds[0]))
        self.failUnless('red' in content)
        self.failUnless('green' in content)
        self.failIf('pink' in content)
        self.failIf('purple' in content)
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicIds[1]))
        self.failUnless('pink' in content)
        self.failUnless('purple' in content)
        self.failIf('red' in content)
        self.failIf('green' in content)
        content = str(self.portal.restrictedTraverse('portal_css/test_rr_2.css'))
        self.failUnless('blue' in content)

class TestPublishing(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()
        self.tool.registerStylesheet('plone_styles.css')
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'index_html')
        self.setRoles(['Member'])

    def testPublishCSSThroughTool(self):
        response = self.publish(self.toolpath + '/plone_styles.css')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'), 'text/css')

    def testPublishNonMagicCSSThroughTool(self):
        self.setRoles(['Manager'])
        body = """<dtml-var "'joined' + 'string'">"""
        self.portal.addDTMLMethod('testmethod', file=body)
        self.tool.registerStylesheet('testmethod')
        response = self.publish(self.toolpath + '/testmethod')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'), 'text/css')

    def testPublishPageWithInlineCSS(self):
        response = self.publish(self.portalpath)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.tool.clearResources()
        # Test that the main page retains its content-type
        self.setRoles(['Manager'])
        body = """<dtml-call "REQUEST.RESPONSE.setHeader('Content-Type', 'text/css')">/*and some css comments too*/"""
        self.portal.addDTMLMethod('testmethod', file=body)
        self.tool.registerStylesheet('testmethod', rendering='inline')
        response = self.publish(self.portalpath)
        self.assertEqual(response.getHeader('Content-Type'), 'text/html;charset=utf-8')
        self.assertEqual(response.getStatus(), 200)

class TestResourcePermissions(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.tool.clearResources()
        self.tool.registerStylesheet('testroot.css', cookable=False)
        self.tool.registerStylesheet('test_rr_1.css')
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.css',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : green }')

        stylesheet = self.portal.restrictedTraverse('testroot.css')

        stylesheet.manage_permission('View',['Manager'], acquire=0)
        stylesheet.manage_permission('Access contents information',['Manager'], acquire=0)
        self.setRoles(['Member'])


    def testUnauthorizedGetItem(self):
        try:
            content = str(self.tool['testroot.css'])
        except Unauthorized:
            return

        self.fail()

    def testUnauthorizedTraversal(self):
        try:
            content = str(self.portal.restrictedTraverse('portal_css/testroot.css'))
        except Unauthorized:
            return

        self.fail()

    def testUnauthorizedOnPublish(self):
        response = self.publish(self.toolpath + '/testroot.css')
        #Will be 302 if CookieCrumbler is enabled
        self.failUnless(response.getStatus() in [302, 403])

    def testRemovedFromResources(self):
        styles = self.tool.getEvaluatedResources(self.portal)
        ids = [item.getId() for item in styles]
        self.failIf('testroot.css' in ids)
        self.failUnless('test_rr_1.css' in self.tool.concatenatedresources[ids[0]])

    def testRemovedFromMergedResources(self):
        self.tool.unregisterResource('testroot.css')
        self.tool.registerStylesheet('testroot.css')
        styles = self.tool.getEvaluatedResources(self.portal)
        magicId = None
        for style in styles:
            id = style.getId()
            if id.startswith(self.tool.filename_base):
                magicId = id
        self.failUnless(magicId)
        content = str(self.portal.restrictedTraverse('portal_css/%s' % magicId))
        self.failIf('green' in content)
        self.failUnless('not authorized' in content)
        self.failUnless('red' in content)

    def testAuthorizedGetItem(self):
        self.setRoles(['Manager'])
        try:
            content = str(self.tool['testroot.css'])
        except Unauthorized:
            self.fail()

    def testAuthorizedTraversal(self):
        self.setRoles(['Manager'])
        try:
            content = str(self.portal.restrictedTraverse('portal_css/testroot.css'))
        except Unauthorized:
            self.fail()

class TestDebugMode(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)
        self.toolpath = '/' + self.tool.absolute_url(1)

    def testDebugModeSplitting(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)
        self.tool.setDebugMode(True)
        self.tool.cookResources()
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 2)

    def testDebugModeSplitting2(self):
        self.tool.registerStylesheet('ham')
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


class TestCSSDefaults(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)

    def testClearingStylesheets(self):
        self.failUnless(self.tool.getResources())
        self.tool.clearResources()
        self.failIf(self.tool.getResources())

    def testDefaultsInstall(self):
        stylesheetids = self.tool.getResourceIds()
        self.failUnless('plone.css' in stylesheetids)
        self.failUnless('ploneColumns.css' in stylesheetids)
        self.failUnless('ploneCustom.css' in stylesheetids)

    def testTraverseToConcatenatedDefaults(self):
        stylesheets = self.tool.getEvaluatedResources(self.portal)
        for s in stylesheets:
            try:
                magicId = s.getId()
                self.portal.restrictedTraverse('portal_css/%s' % magicId)
            except KeyError:
                self.fail()

    def testCallingOfConcatenatedStylesheets(self):
        stylesheets = self.tool.getEvaluatedResources(self.portal)
        for s in stylesheets:
            if 'ploneStyles' in s.getId():
                output = self.portal.restrictedTraverse('portal_css/%s' % s.getId())
                break
        if not output:
            self.fail()
        o = str(output)[:]
        self.failIf('&lt;dtml-call' in o)
        self.failIf('&amp;dtml-fontBaseSize;' in o)
        self.failUnless('** Plone style sheet for CSS2-capable browsers.' in o)


class TestResourceObjects(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()

    def testSetEnabled(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])
        spam = self.tool.getResource('spam')
        spam.setEnabled(False)
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])
        self.tool.cookResources()
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'eggs'])

    def testSetCookable(self):
        self.tool.registerStylesheet('ham')
        self.tool.registerStylesheet('spam')
        self.tool.registerStylesheet('eggs')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])
        spam = self.tool.getResource('spam')
        spam.setCookable(False)
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])
        self.tool.cookResources()
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham'])
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[1].getId()],
                         ['spam'])
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[2].getId()],
                         ['eggs'])




def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestImplementation))
    suite.addTest(makeSuite(TestTool))
    suite.addTest(makeSuite(TestSkin))
    suite.addTest(makeSuite(testZMIMethods))
    suite.addTest(makeSuite(TestStylesheetRegistration))
    suite.addTest(makeSuite(TestStylesheetRenaming))
    suite.addTest(makeSuite(TestToolSecurity))
    suite.addTest(makeSuite(TestToolExpression))
    suite.addTest(makeSuite(TestStylesheetCooking))
    suite.addTest(makeSuite(TestPublishing))
    suite.addTest(makeSuite(TestStylesheetMoving))
    suite.addTest(makeSuite(TestTraversal))
    suite.addTest(makeSuite(TestZODBTraversal))
    suite.addTest(makeSuite(TestMergingDisabled))
    suite.addTest(makeSuite(TestResourcePermissions))
    suite.addTest(makeSuite(TestDebugMode))
    suite.addTest(makeSuite(TestResourceObjects))

    if not PLONE21:
        # We must not test for the defaults in Plone 2.1 because they are
        # all different. Plone2.1 has tests in CMFPlone/tests for defaults
        # and migrations
        suite.addTest(makeSuite(TestCSSDefaults))

    return suite

if __name__ == '__main__':
    framework()
