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

class TestHTTPHeaders(CSSRegistryTestCase.CSSRegistryTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal, CSSTOOLNAME)
        self.tool.clearResources()
        self.toolpath = '/' + self.tool.absolute_url(1)
        self.portalpath = '/' + getToolByName(self.portal, 'portal_url')(1)

    def testContentTypeHeaders(self):
        # Test that the main page retains its content-type
        self.setRoles(['Manager'])
        # we make a method that tries to set its own Content-Type headers
        self.portal.addDTMLMethod('testmethod', file="""<dtml-call "REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')">""")
        self.tool.registerStylesheet('testmethod')
        response = self.publish(self.toolpath+'/testmethod')
        self.assertEqual(response.getHeader('Content-Type'), 'text/css')
        self.assertEqual(response.getStatus(), 200)

    def testIfModifiedSinceHeaders1(self):
        # test with if-modified-since headers early and late (since client clock won't necessarily be synchronized)
        
        # Test that the main page retains its content-type
        self.setRoles(['Manager'])
        #self.portal.REQUEST.set('If-Modified-Since', rfc1123_date((DateTime() - 60.0/(24.0*3600.0)).timeTime())) # if modified in the last minute
        request = self.portal.REQUEST
        request.environ['IF_MODIFIED_SINCE'] = rfc1123_date((DateTime() - 60.0/(24.0*3600.0))) # if modified in the last minute
        print '###################################'
        print 'if-modified-since: ', request.get_header('If-Modified-Since', None)
        assert request.get_header('If-Modified-Since')
        self.portal.addDTMLMethod('testmethod', file="""/* YES WE ARE RENDERED */""")
        self.tool.registerStylesheet('testmethod')
        response = self.publish(self.toolpath+'/testmethod')
        self.assertEqual(response.getHeader('Content-Type'), 'text/css')
        self.assertEqual(response.getStatus(), 200)

    def testIfModifiedSinceHeaders2(self):
        # test with if-modified-since headers early and late (since client clock won't necessarily be synchronized)

        # Test that the main page retains its content-type
        self.setRoles(['Manager'])
        #self.portal.REQUEST.set('If-Modified-Since', rfc1123_date((DateTime() + 60.0/(24.0*3600.0)).timeTime())) # if modified in the last minute
        request = self.portal.REQUEST
        #print request.environ
        #request.get_header('IF_MODIFIED_SINCE', None)
        request.environ['IF_MODIFIED_SINCE'] = rfc1123_date((DateTime() + 60.0/(24.0*3600.0))) # if modified in the last minute
        print '###################################'
        print 'if-modified-since: ', request.get_header('If-Modified-Since', None)
        assert request.get_header('If-Modified-Since')
        self.portal.addDTMLMethod('testmethod2', file="""/* YES WE ARE RENDERED */""")
        self.tool.registerStylesheet('testmethod2')
        response = self.publish(self.toolpath+'/testmethod2')
        self.assertEqual(response.getHeader('Content-Type'), 'text/css')
        self.assertEqual(response.getStatus(), 200)


    def testContentLengthHeaders(self):
        # Test that the main page retains its content-type
        self.setRoles(['Manager'])
        self.portal.REQUEST.set('If-Modified-Since', rfc1123_date((DateTime() - 1).timeTime()))
        print self.portal.REQUEST.get('If-Modified-Since')
        self.tool.registerStylesheet('test_rr_1.css')
        self.portal.addDTMLMethod('testmethod', file="""/* YES WE ARE RENDERED */""")
        self.tool.registerStylesheet('testmethod')
        self.portal.addDTMLMethod('testmethod2', file="""/* YES WE ARE RENDERED 2 */""")
        self.tool.registerStylesheet('testmethod2')
        # we also add an fsfile for good measure
        self.tool.registerStylesheet('test_rr_2.css')
        rs = self.tool.getEvaluatedResources(self.portal)
        self.assertEqual(len(rs),1)
        response = self.publish(self.toolpath+'/'+rs[0].getId())
        self.assertEqual(response.getHeader('Content-Type'), 'text/css')
        print str(response)
        self.assertEqual(int(response.getHeader('content-length')), len(response.getBody()))
        self.assertEqual(response.getStatus(), 200)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestHTTPHeaders))

    return suite

if __name__ == '__main__':
    framework()
