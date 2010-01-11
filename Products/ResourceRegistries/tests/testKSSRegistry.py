#
# CSSRegistry Tests
#
from zope.component import getMultiAdapter
from zope.contentprovider.interfaces import IContentProvider

from App.Common import rfc1123_date
from DateTime import DateTime
from AccessControl import Unauthorized
from zope.interface.verify import verifyObject

from Products.CMFCore.Expression import Expression
from Products.CMFCore.utils import getToolByName

from Products.PloneTestCase.PloneTestCase import portal_owner, default_password

from Products.ResourceRegistries.config import KSSTOOLNAME
from Products.ResourceRegistries.interfaces import IKSSRegistry
from Products.ResourceRegistries.interfaces import ICookedFile
from Products.ResourceRegistries.tests.RegistryTestCase import RegistryTestCase
from Products.ResourceRegistries.tests.RegistryTestCase import FunctionalRegistryTestCase


class KSSRegistryTestCase(RegistryTestCase):

    def afterSetUp(self):
        tool = getattr(self.portal, KSSTOOLNAME, None)
        if tool is None:
            from Products.ResourceRegistries.tools import KSSRegistry
            kss = KSSRegistry.KSSRegistryTool()
            self.portal[KSSTOOLNAME] = kss
        self.tool = getattr(self.portal, KSSTOOLNAME)


class FunctionalKSSRegistryTestCase(
        KSSRegistryTestCase,
        FunctionalRegistryTestCase
    ):
    pass


class TestImplementation(KSSRegistryTestCase):

    def test_interfaces(self):
        tool = getattr(self.portal, KSSTOOLNAME)
        self.failUnless(IKSSRegistry.providedBy(tool))
        self.failUnless(verifyObject(IKSSRegistry, tool))


class TestTool(KSSRegistryTestCase):

    def testToolExists(self):
        self.failUnless(KSSTOOLNAME in self.portal.objectIds())

    def testZMIForm(self):
        tool = getattr(self.portal, KSSTOOLNAME)
        self.setRoles(['Manager'])
        self.failUnless(tool.manage_kssForm())
        self.failUnless(tool.manage_kssComposition())


class testZMIMethods(KSSRegistryTestCase):

    def testAdd(self):
        self.tool.clearResources()
        self.tool.manage_addKineticStylesheet(id='joe')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.failUnless(self.tool.getResources())


class TestKineticStylesheetRegistration(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()

    def testStoringKineticStylesheet(self):
        self.tool.registerKineticStylesheet('foo')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.assertEqual(self.tool.getResources()[0].getId(), 'foo')

    def testDefaultKineticStylesheetAttributes(self):
        self.tool.registerKineticStylesheet('foodefault')
        self.assertEqual(self.tool.getResources()[0].getId(), 'foodefault')
        self.assertEqual(self.tool.getResources()[0].getExpression(), '')
        self.failUnless(self.tool.getResources()[0].getEnabled())

    def testKineticStylesheetAttributes(self):
        self.tool.registerKineticStylesheet('foo', expression='python:1',
                                            enabled=0)
        self.assertEqual(self.tool.getResources()[0].getId(), 'foo')
        self.assertEqual(self.tool.getResources()[0].getExpression(), 'python:1')
        self.failIf(self.tool.getResources()[0].getEnabled())

    def testDisallowingDuplicateIds(self):
        self.tool.registerKineticStylesheet('foo')
        self.assertRaises(ValueError, self.tool.registerKineticStylesheet, 'foo')

    def testUnregisterKineticStylesheet(self):
        self.tool.registerKineticStylesheet('foo')
        self.assertEqual(len(self.tool.getResources()), 1)
        self.assertEqual(self.tool.getResources()[0].getId(), 'foo')
        self.tool.unregisterResource('foo')
        self.assertEqual(len(self.tool.getResources()), 0)

    def testKineticStylesheetsDict(self):
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('ham')
        keys = self.tool.getResourcesDict().keys()
        keys.sort()
        res = ['ham', 'spam']
        res.sort()
        self.assertEqual(res, keys)
        self.assertEqual(self.tool.getResourcesDict()['ham'].getId(), 'ham')


class TestKineticStylesheetRenaming(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()

    def testRenaming(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])
        self.tool.renameResource('spam', 'bacon')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'bacon', 'eggs'])

    def testRenamingIdClash(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertRaises(ValueError, self.tool.renameResource, 'spam', 'eggs')

    def testDoubleRenaming(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.tool.renameResource('spam', 'bacon')
        self.assertRaises(ValueError, self.tool.renameResource, 'spam', 'bacon')


class TestToolSecurity(KSSRegistryTestCase):

    def testRegistrationSecurity(self):
        self.tool.clearResources()
        self.assertRaises(Unauthorized, self.tool.restrictedTraverse,
                          'registerKineticStylesheet')
        self.assertRaises(Unauthorized, self.tool.restrictedTraverse,
                          'unregisterResource')
        self.setRoles(['Manager'])
        try:
            self.tool.restrictedTraverse('registerKineticStylesheet')
            self.tool.restrictedTraverse('unregisterResource')
        except Unauthorized:
            self.fail()


class TestToolExpression(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()

    def testSimplestExpression(self):
        context = self.portal
        self.failUnless(self.tool.evaluateExpression(
            Expression('python:1'), context))
        self.failIf(self.tool.evaluateExpression(
            Expression('python:0'), context))
        self.failUnless(self.tool.evaluateExpression(
            Expression('python:0+1'), context))

    def testNormalExpression(self):
        context = self.portal
        self.failUnless(self.tool.evaluateExpression(
            Expression('object/absolute_url'), context))

    def testExpressionInFolder(self):
        self.folder.invokeFactory('Document', 'eggs')
        context = self.folder
        self.failUnless(self.tool.evaluateExpression(
            Expression('python:"eggs" in object.objectIds()'), context))


class TestKineticStylesheetCooking(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()

    def testKineticStylesheetCooking(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 1)
        self.assertEqual(len(self.tool.concatenatedresources.keys()), 4)

    def testKineticStylesheetCookingValues(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.concatenatedresources[
                         self.tool.cookedresources[0].getId()],
                         ['ham', 'spam', 'eggs'])

    def testGetEvaluatedKineticStylesheetsCollapsing(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testMoreComplexKineticStylesheetsCollapsing(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam', expression='string:spam')
        self.tool.registerKineticStylesheet('spam spam', expression='string:spam')
        self.tool.registerKineticStylesheet('spam spam spam', expression='string:spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 3)
        magic_ids = [item.getId() for item in self.tool.getEvaluatedResources(self.folder)]
        self.failUnless('ham' in self.tool.concatenatedresources[magic_ids[0]])
        self.failUnless('eggs' in self.tool.concatenatedresources[magic_ids[2]])
        self.failUnless('spam' in self.tool.concatenatedresources[magic_ids[1]])
        self.failUnless('spam spam' in self.tool.concatenatedresources[magic_ids[1]])
        self.failUnless('spam spam spam' in self.tool.concatenatedresources[magic_ids[1]])

    def testGetEvaluatedKineticStylesheetsWithExpression(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam', expression='python:1')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 2)

    def testGetEvaluatedKineticStylesheetsWithFailingExpression(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam', expression='python:0')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testGetEvaluatedKineticStylesheetsWithContextualExpression(self):
        self.folder.invokeFactory('Document', 'eggs')
        self.tool.registerKineticStylesheet('spam', expression='python:"eggs" in object.objectIds()')
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)

    def testCollapsingKineticStylesheetsLookup(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam', expression='string:ham')
        self.tool.registerKineticStylesheet('spam spam', expression='string:ham')
        evaluated = self.tool.getEvaluatedResources(self.folder)
        self.assertEqual(len(evaluated), 2)

    def testRenderingIsInTheRightOrder(self):
        self.tool.registerKineticStylesheet('ham', expression='string:ham')
        self.tool.registerKineticStylesheet('spam', expression='string:spam')
        evaluated = self.tool.getEvaluatedResources(self.folder)
        magic_ids = [item.getId() for item in evaluated]
        ids = []
        for magic_id in magic_ids:
            self.assertEqual(len(self.tool.concatenatedresources[magic_id]), 1)
            ids.append(self.tool.concatenatedresources[magic_id][0])
        self.failUnless(ids[0] == 'ham')
        self.failUnless(ids[1] == 'spam')

    def testConcatenatedSheetsAreInTheRightOrderToo(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        evaluated = self.tool.getEvaluatedResources(self.folder)
        results = self.tool.concatenatedresources[evaluated[0].getId()]
        self.failUnless(results[0] == 'ham')
        self.failUnless(results[1] == 'spam')
        self.failUnless(results[2] == 'eggs')


class TestKineticStylesheetMoving(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()

    def testKineticStylesheetMoveDown(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceDown('spam')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'eggs', 'spam'))

    def testKineticStylesheetMoveDownAtEnd(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceDown('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))

    def testKineticStylesheetMoveUp(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceUp('spam')
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'ham', 'eggs'))

    def testKineticStylesheetMoveUpAtStart(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceUp('ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))

    def testKineticStylesheetMoveIllegalId(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.assertRaises(ValueError, self.tool.moveResourceUp, 'foo')

    def testKineticStylesheetMoveToBottom(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceToBottom('ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'eggs', 'ham'))

    def testKineticStylesheetMoveToTop(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs'))
        self.tool.moveResourceToTop('eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('eggs', 'ham', 'spam'))

    def testKineticStylesheetMoveBefore(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.tool.registerKineticStylesheet('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResourceBefore('bacon', 'ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('bacon', 'ham', 'spam', 'eggs'))
        self.tool.moveResourceBefore('bacon', 'eggs')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'bacon', 'eggs'))

    def testKineticStylesheetMoveAfter(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.tool.registerKineticStylesheet('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResourceAfter('bacon', 'ham')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'bacon', 'spam', 'eggs'))
        self.tool.moveResourceAfter('bacon', 'spam')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'bacon', 'eggs'))

    def testKineticStylesheetMove(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
        self.tool.registerKineticStylesheet('bacon')
        self.assertEqual(self.tool.getResourceIds(),
                         ('ham', 'spam', 'eggs', 'bacon'))
        self.tool.moveResource('ham', 2)
        self.assertEqual(self.tool.getResourceIds(),
                         ('spam', 'eggs', 'ham', 'bacon'))
        self.tool.moveResource('bacon', 0)
        self.assertEqual(self.tool.getResourceIds(),
                         ('bacon', 'spam', 'eggs', 'ham'))


class TestTraversal(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()
        self.tool.registerKineticStylesheet('test_rr_1.kss')

    def testMarker(self):
        traversed = self.portal.restrictedTraverse('portal_kss/test_rr_1.kss')
        self.failUnless(ICookedFile.providedBy(traversed))
    
    def testMarkerComposite(self):
        self.tool.registerKineticStylesheet('test_rr_2.kss')
        scripts = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(scripts), 1)
        magicId = scripts[0].getId()
        traversed = self.portal.restrictedTraverse('portal_kss/%s' % magicId)
        self.failUnless(ICookedFile.providedBy(traversed))

    def testGetItemTraversal(self):
        self.failUnless(self.tool['test_rr_1.kss'])

    def testGetItemTraversalContent(self):
        self.failUnless('background-color' in str(self.tool['test_rr_1.kss']))

    def testRestrictedTraverseContent(self):
        self.failUnless('background-color' in str(
                        self.portal.restrictedTraverse('portal_kss/test_rr_1.kss')))

    def testRestrictedTraverseComposition(self):
        self.tool.registerKineticStylesheet('test_rr_2.kss')
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 1)
        magicId = styles[0].getId()
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicId))
        self.failUnless('background-color' in content)
        self.failUnless('blue' in content)

    def testCompositesWithBrokedId(self):
        self.tool.registerKineticStylesheet('nonexistant.kss')
        stylesheets = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(stylesheets), 1)
        magicId = stylesheets[0].getId()
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicId))


class TestZODBTraversal(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.kss',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : red }')
        self.portal.invokeFactory('Folder', 'subfolder')
        self.portal.subfolder.invokeFactory('File',
                                   id='testsubfolder.kss',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : blue }')

        self.tool.registerKineticStylesheet('testroot.kss')
        self.tool.registerKineticStylesheet('subfolder/testsubfolder.kss')
        self.setRoles(['Member'])

    def testGetItemTraversal(self):
        self.failUnless(self.tool['testroot.kss'])
        self.failUnless(self.tool['subfolder/testsubfolder.kss'])

    def testGetItemTraversalContent(self):
        self.failUnless('red' in str(self.tool['testroot.kss']))
        self.failUnless('blue' in str(self.tool['subfolder/testsubfolder.kss']))
        self.failIf('blue' in str(self.tool['testroot.kss']))
        self.failIf('red' in str(self.tool['subfolder/testsubfolder.kss']))


    def testRestrictedTraverseContent(self):
        self.failUnless('red' in str(
                        self.portal.restrictedTraverse('portal_kss/testroot.kss')))
        self.failUnless('blue' in str(
                        self.portal.restrictedTraverse('portal_kss/subfolder/testsubfolder.kss')))
        self.failIf('blue' in str(
                        self.portal.restrictedTraverse('portal_kss/testroot.kss')))
        self.failIf('red' in str(
                        self.portal.restrictedTraverse('portal_kss/subfolder/testsubfolder.kss')))

    def testRestrictedTraverseComposition(self):
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 1)
        magicId = styles[0].getId()
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicId))
        self.failUnless('background-color' in content)
        self.failUnless('red' in content)
        self.failUnless('blue' in content)


class TestMergingDisabled(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()
        self.tool.registerKineticStylesheet('testroot.kss')
        self.tool.registerKineticStylesheet('test_rr_1.kss')
        self.tool.registerKineticStylesheet('test_rr_2.kss', cookable=False)
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.kss',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : green }')
        self.setRoles(['Member'])

    def testDefaultKineticStylesheetCookableAttribute(self):
        self.failUnless(self.tool.getResources()[self.tool.getResourcePosition('test_rr_1.kss')].getCookable())
        self.failUnless(self.tool.getResources()[self.tool.getResourcePosition('testroot.kss')].getCookable())

    def testKineticStylesheetCookableAttribute(self):
        self.failIf(self.tool.getResources()[self.tool.getResourcePosition('test_rr_2.kss')].getCookable())

    def testNumberOfResources(self):
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 5)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 2)

    def testCompositionWithLastUncooked(self):
        self.tool.moveResourceToBottom('test_rr_2.kss')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 5)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 2)
        magicIds = []
        for style in styles:
            id = style.getId()
            if '-cachekey' in id:
                magicIds.append(id)
        self.failUnless(magicIds[-1].startswith('test_rr_2'))
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicIds[-2]))
        self.failUnless('red' in content)
        self.failUnless('green' in content)
        self.failIf('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicIds[-1]))
        self.failIf('red' in content)
        self.failIf('green' in content)
        self.failUnless('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_kss/test_rr_2.kss'))
        self.failUnless('blue' in content)

    def testCompositionWithFirstUncooked(self):
        self.tool.moveResourceToTop('test_rr_2.kss')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 2)
        self.assertEqual(len(self.tool.concatenatedresources), 5)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 2)
        magicId = None
        for style in styles:
            id = style.getId()
            if '-cachekey' in id:
                magicId = id
        self.failUnless(magicId)
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicId))
        self.failUnless('red' in content)
        self.failUnless('green' in content)
        self.failIf('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_kss/test_rr_2.kss'))
        self.failUnless('blue' in content)

    def testCompositionWithMiddleUncooked(self):
        self.tool.moveResourceToTop('test_rr_2.kss')
        self.tool.moveResourceDown('test_rr_2.kss')
        self.assertEqual(len(self.tool.getResources()), 3)
        self.assertEqual(len(self.tool.cookedresources), 3)
        self.assertEqual(len(self.tool.concatenatedresources), 6)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 3)
        content = str(self.portal.restrictedTraverse('portal_kss/test_rr_2.kss'))
        self.failUnless('blue' in content)
        content = str(self.portal.restrictedTraverse('portal_kss/test_rr_1.kss'))
        self.failUnless('red' in content)
        content = str(self.portal.restrictedTraverse('portal_kss/testroot.kss'))
        self.failUnless('green' in content)

    def testLargerCompositionWithMiddleUncooked(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testpurple.kss',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : purple }')
        self.portal.invokeFactory('File',
                                   id='testpink.kss',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : pink }')
        self.setRoles(['Member'])
        self.tool.registerKineticStylesheet('testpurple.kss')
        self.tool.registerKineticStylesheet('testpink.kss')
        self.tool.moveResourceToTop('test_rr_2.kss')
        self.tool.moveResourceDown('test_rr_2.kss', 2)
        #Now have [[green,red],blue,[purple,pink]]
        self.assertEqual(len(self.tool.getResources()), 5)
        self.assertEqual(len(self.tool.cookedresources), 3)
        self.assertEqual(len(self.tool.concatenatedresources), 8)
        styles = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(styles), 3)
        magicIds = []
        for style in styles:
            id = style.getId()
            if '-cachekey' in id:
                magicIds.append(id)
        self.assertEqual(len(magicIds), 3)
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicIds[0]))
        self.failUnless('red' in content)
        self.failUnless('green' in content)
        self.failIf('pink' in content)
        self.failIf('purple' in content)
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicIds[2]))
        self.failUnless('pink' in content)
        self.failUnless('purple' in content)
        self.failIf('red' in content)
        self.failIf('green' in content)
        content = str(self.portal.restrictedTraverse('portal_kss/test_rr_2.kss'))
        self.failUnless('blue' in content)

class TestPublishing(FunctionalKSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()
        self.tool.registerKineticStylesheet('plone_styles.kss')
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.portalpath = '/' + getToolByName(self.portal, "portal_url")(1)
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'index_html')
        self.setRoles(['Member'])

    def testPublishCSSThroughTool(self):
        response = self.publish(self.toolpath + '/plone_styles.kss')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'), 'text/css;charset=utf-8')

    def testPublishNonMagicCSSThroughTool(self):
        self.setRoles(['Manager'])
        body = """<dtml-var "'joined' + 'string'">"""
        self.portal.addDTMLMethod('testmethod', file=body)
        self.tool.registerKineticStylesheet('testmethod')
        response = self.publish(self.toolpath + '/testmethod')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type'), 'text/css;charset=utf-8')


class TestFivePublishing(FunctionalKSSRegistryTestCase):
    'Publishing with Five'

    def afterSetUp(self):
        # Define some resource
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()
        self.tool.registerKineticStylesheet('++resource++test_rr_1.kss')
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.portalpath = '/' + getToolByName(self.portal, "portal_url")(1)
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'index_html')
        self.setRoles(['Member'])

    def testPublishFiveResource(self):
        response = self.publish(self.toolpath + '/++resource++test_rr_1.kss')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Type')[:10], 'text/plain')
        self.assertEqual('body { background-color : red }' in response.getBody(), True)


class TestResourcePermissions(FunctionalKSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.tool.clearResources()
        self.tool.registerKineticStylesheet('testroot.kss', cookable=False)
        self.tool.registerKineticStylesheet('test_rr_1.kss')
        self.setRoles(['Manager'])
        self.portal.invokeFactory('File',
                                   id='testroot.kss',
                                   format='text/css',
                                   content_type='text/css',
                                   file='body { background-color : green }')

        stylesheet = getattr(self.portal, 'testroot.kss')

        stylesheet.manage_permission('View',['Manager'], acquire=0)
        stylesheet.manage_permission('Access contents information',['Manager'], acquire=0)
        self.setRoles(['Member'])


    def testUnauthorizedGetItem(self):
        try:
            content = str(self.tool['testroot.kss'])
        except Unauthorized:
            return

        self.fail()

    def testUnauthorizedTraversal(self):
        try:
            content = str(self.portal.restrictedTraverse('portal_kss/testroot.kss'))
        except Unauthorized:
            return

        self.fail()

    def testUnauthorizedOnPublish(self):
        response = self.publish(self.toolpath + '/testroot.kss')
        #Will be 302 if CookieCrumbler is enabled
        self.failUnless(response.getStatus() in [302, 403, 401])

    def testRemovedFromResources(self):
        styles = self.tool.getEvaluatedResources(self.portal)
        ids = [item.getId() for item in styles]
        self.assertEqual(len(self.tool.concatenatedresources), 4)
        self.failIf('testroot.kss' in ids)
        self.failUnless('test_rr_1.kss' in self.tool.concatenatedresources[ids[1]])

    def testRemovedFromMergedResources(self):
        self.tool.unregisterResource('testroot.kss')
        self.tool.registerKineticStylesheet('testroot.kss')
        styles = self.tool.getEvaluatedResources(self.portal)
        magicId = None
        for style in styles:
            id = style.getId()
            if '-cachekey' in id:
                magicId = id
        self.failUnless(magicId)
        content = str(self.portal.restrictedTraverse('portal_kss/%s' % magicId))
        self.failIf('green' in content)
        self.failUnless('not authorized' in content)
        self.failUnless('red' in content)

    def testAuthorizedGetItem(self):
        self.setRoles(['Manager'])
        try:
            content = str(self.tool['testroot.kss'])
        except Unauthorized:
            self.fail()

    def testAuthorizedTraversal(self):
        self.setRoles(['Manager'])
        try:
            content = str(self.portal.restrictedTraverse('portal_kss/testroot.kss'))
        except Unauthorized:
            self.fail()

    def testAuthorizedOnPublish(self):
        authstr = "%s:%s" % (portal_owner, default_password)
        response = self.publish(self.toolpath + '/testroot.kss', basic=authstr)
        self.failUnlessEqual(response.getStatus(), 200)

class TestDebugMode(FunctionalKSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()
        self.portalpath = '/' + getToolByName(self.portal, "portal_url")(1)
        self.toolpath = '/' + self.tool.absolute_url(1)

    def testDebugModeSplitting(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.setDebugMode(False)
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 1)
        self.tool.setDebugMode(True)
        self.assertEqual(len(self.tool.getEvaluatedResources(self.folder)), 2)

    def testDebugModeSplitting2(self):
        self.tool.registerKineticStylesheet('ham')
        now = DateTime()
        days = 7
        soon = now + days
        self.tool.setDebugMode(True)
        # Publish in debug mode
        response = self.publish(self.toolpath+'/ham')
        self.failIfEqual(response.getHeader('Expires'), rfc1123_date(soon.timeTime()))
        self.assertEqual(response.getHeader('Expires'), rfc1123_date(now.timeTime()))
        self.assertEqual(response.getHeader('Cache-Control'), 'max-age=0')


class TestResourceObjects(KSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.tool.clearResources()

    def testSetEnabled(self):
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
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
        self.tool.registerKineticStylesheet('ham')
        self.tool.registerKineticStylesheet('spam')
        self.tool.registerKineticStylesheet('eggs')
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


class TestSkinAwareness(FunctionalKSSRegistryTestCase):

    def afterSetUp(self):
        KSSRegistryTestCase.afterSetUp(self)
        self.skinstool = getattr(self.portal, 'portal_skins')
        self.tool.clearResources()
        self.portalpath = '/' + getToolByName(self.portal, "portal_url")(1)
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.setRoles(['Manager'])
        self.skinstool.manage_addFolder(id='pink')
        self.skinstool.manage_addFolder(id='purple')
        self.skinstool.pink.manage_addFile(id='skin.kss',
                                   content_type='text/css',
                                   file='body { background-color : pink }')
        self.skinstool.purple.manage_addFile(id='skin.kss',
                                    content_type='text/css',
                                    file='body { background-color : purple }')
        self.tool.registerKineticStylesheet('skin.kss')
        self.skinstool.addSkinSelection('PinkSkin', 'pink,ResourceRegistries')
        self.skinstool.addSkinSelection('PurpleSkin', 'purple,ResourceRegistries')
        self.setRoles(['Member'])
        
    def testRenderIncludesSkinInPath(self):
        self.portal.changeSkin('PinkSkin', REQUEST=self.portal.REQUEST)
        view = self.portal.restrictedTraverse('@@plone')
        viewletmanager = getMultiAdapter((self.portal, self.portal.REQUEST, view), IContentProvider, name = u'plone.resourceregistries.styles')
        viewletmanager.update()
        content = viewletmanager.render()
        self.failUnless('/PinkSkin/' in content)
        self.failIf('/PurpleSkin/' in content)
        self.portal.changeSkin('PurpleSkin', REQUEST=self.portal.REQUEST)
        view = self.portal.restrictedTraverse('@@plone')
        viewletmanager = getMultiAdapter((self.portal, self.portal.REQUEST, view), IContentProvider, name = u'plone.resourceregistries.styles')
        viewletmanager.update()
        content = viewletmanager.render()
        self.failUnless('/PurpleSkin/' in content)
        self.failIf('/PinkSkin/' in content)

    def testPublishWithSkin(self):
        response = self.publish(self.toolpath + '/PinkSkin/skin.kss')
        self.assertEqual(response.getStatus(), 200)
        self.failUnless('pink' in str(response))
        response = self.publish(self.toolpath + '/PurpleSkin/skin.kss')
        self.assertEqual(response.getStatus(), 200)
        self.failUnless('purple' in str(response))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestImplementation))
    suite.addTest(makeSuite(TestTool))
    suite.addTest(makeSuite(testZMIMethods))
    suite.addTest(makeSuite(TestKineticStylesheetRegistration))
    suite.addTest(makeSuite(TestKineticStylesheetRenaming))
    suite.addTest(makeSuite(TestToolSecurity))
    suite.addTest(makeSuite(TestToolExpression))
    suite.addTest(makeSuite(TestKineticStylesheetCooking))
    suite.addTest(makeSuite(TestPublishing))
    suite.addTest(makeSuite(TestFivePublishing))
    suite.addTest(makeSuite(TestKineticStylesheetMoving))
    suite.addTest(makeSuite(TestTraversal))
    suite.addTest(makeSuite(TestZODBTraversal))
    suite.addTest(makeSuite(TestMergingDisabled))
    suite.addTest(makeSuite(TestResourcePermissions))
    suite.addTest(makeSuite(TestDebugMode))
    suite.addTest(makeSuite(TestResourceObjects))
    suite.addTest(makeSuite(TestSkinAwareness))

    return suite
