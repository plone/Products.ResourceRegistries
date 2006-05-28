'''\
Set up tests with Five.
'''

import Products.ResourceRegistries.tests
from textwrap import dedent

class FiveTestsBase:
    'Publishing with Five'

    def afterSetUp(self):
        from zope.app.testing.placelesssetup import setUp
        setUp()
        # Allow traversing
        import Products.Five
        from Products.Five.zcml import load_string, load_config
        load_config('meta.zcml', package=Products.Five)
        load_config('configure.zcml', package=Products.Five)
        # Change to the context of this package
        Products.Five.zcml._context.package = Products.ResourceRegistries.tests
        load_string(dedent('''\
                    <configure xmlns="http://namespaces.zope.org/zope"
                           xmlns:five="http://namespaces.zope.org/five">
                    <include package="zope.app.traversing" />
                    <adapter
                          for="*"
                          factory="Products.Five.traversable.FiveTraversable"
                          provides="zope.app.traversing.interfaces.ITraversable"
                          />
                    <adapter
                          for="*"
                          factory="zope.app.traversing.adapters.Traverser"
                          provides="zope.app.traversing.interfaces.ITraverser"
                          />
                    </configure>'''))
        # Enable Plone traversing
        # XXX this is needed in 2.1 but if defined it breaks 2.5. Why?
        load_string(dedent('''\
                    <configure xmlns="http://namespaces.zope.org/zope"
                           xmlns:five="http://namespaces.zope.org/five">
                      <!-- IPortal binds to the portal root -->

                      <interface
                          interface=".interfaces.IPortal"
                          type="zope.app.content.interfaces.IContentType"
                          />

                      <five:traversable class="Products.CMFPlone.Portal.PloneSite" />

                      <content class="Products.CMFPlone.Portal.PloneSite">
                        <implements
                            interface=".interfaces.IPortal"
                            />
                        <!--require
                            permission="zope.View"
                            interface=".interfaces.IPortal"
                            /-->
                      </content>

                      <!-- IPortalObject binds to all portal objects -->
                      
                      <interface
                          interface=".interfaces.IPortalObject"
                          type="zope.app.content.interfaces.IContentType"
                          />
                     
                      <five:implements
                          class="Products.CMFCore.PortalObject.PortalObjectBase"
                          interface=".interfaces.IPortalObject"
                          />
                      <five:implements
                          class="Products.Archetypes.public.BaseObject"
                          interface=".interfaces.IPortalObject"
                          />
                     
                      <five:traversable class="Products.CMFCore.PortalObject.PortalObjectBase" />
                      <five:traversable class="Products.Archetypes.public.BaseObject" />

                    </configure>'''))

    def beforeTearDown(self):
        from zope.app.testing.placelesssetup import tearDown
        tearDown()
        import Products.Five.zcml
        Products.Five.zcml._context = None
