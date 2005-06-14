import random

from DateTime import DateTime
from zExceptions import NotFound
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from OFS.Image import File
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager

from Acquisition import aq_base, aq_parent, aq_inner

from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import IResourceRegistry


class BaseRegistryTool(UniqueObject, SimpleItem, PropertyManager):
    """Base class for a Plone registry managing resource files."""

    security = ClassSecurityInfo()
    __implements__ = (SimpleItem.__implements__, IResourceRegistry)
    manage_options = SimpleItem.manage_options

    #
    # Private Methods
    #

    def __init__(self):
        """Add the storages."""
        self.resources = ()
        self.cookedresources = ()
        self.concatenatedresources = {}
        self.debugmode = False
        self.attributes_to_compare = ('expression',)
        self.filename_base = 'ploneResources'
        self.filename_appendix = '.res'
        self.merged_output_prefix = ''
        self.cache_duration = 3600

    def __getitem__(self, item):
        """Return a resource from the registry."""
        output = self.getResource(item, self)
        if self.getDebugMode():
            duration = 0
        else:
            duration = self.cache_duration
        self.REQUEST.RESPONSE.setHeader('Expires',
            (DateTime() + duration).strftime('%a, %d %b %Y %H:%M:%S %Z'))
        contenttype = self.getContentType()
        return File(item, item, output, contenttype).__of__(self)

    def __bobo_traverse__(self, REQUEST, name):
        """Traversal hook."""
        if REQUEST is not None and \
           self.concatenatedresources.get(name, None) is not None:
            return self.__getitem__(name)
        obj = getattr(self, name, None)
        if obj is not None:
            return obj
        raise AttributeError('%s' % (name,))

    security.declarePrivate('validateId')
    def validateId(self, id, existing):
        """Safeguard against duplicate ids."""
        for sheet in existing:
            if sheet.get('id') == id:
                raise ValueError, 'Duplicate id %s' %(id)

    security.declarePrivate('storeResource')
    def storeResource(self, resource):
        """Store a resource."""
        self.validateId(resource.get('id'), self.getResources())
        resources = list(self.resources)
        resources.append(resource)
        self.resources = tuple(resources)
        self.cookResources()

    security.declarePrivate('clearResources')
    def clearResources(self):
        """Clears all resource data.

        Convenience funtion for Plone migrations and tests.
        """
        self.resources = ()
        self.cookedresources = ()
        self.concatenatedresources = {}

    security.declarePrivate('getResourcesDict')
    def getResourcesDict(self):
        """Get the resources as a dictionary instead of an ordered list.

        Good for lookups. Internal.
        """
        resources = self.getResources()
        d = {}
        for s in resources:
            d[s['id']] = s
        return d

    security.declarePrivate('compareResources')
    def compareResources(self, s1, s2):
        """Check if two resources are compatible."""
        for attr in self.attributes_to_compare:
            if s1.get(attr) != s2.get(attr):
                return False
        return True

    security.declarePrivate('generateId')
    def generateId(self):
        """Generate a random id."""
        return '%s%04d%s' % (self.filename_base, random.randint(0, 9999),
                             self.filename_appendix)

    security.declarePrivate('finalizeResourceMerging')
    def finalizeResourceMerging(self, resource, previtem):
        """Finalize the resource merging with the previous item.

        Might be overwritten in subclasses.
        """
        pass

    security.declarePrivate('finalizeContent')
    def finalizeContent(self, resource, content):
        """Finalize the resource content.

        Might be overwritten in subclasses.
        """
        return content

    security.declarePrivate('cookResources')
    def cookResources(self):
        """Cook the stored resources."""
        resources = [r for r in self.getResources() if r.get('enabled')]
        self.concatenatedresources = {}
        self.cookedresources = ()
        results = []
        for resource in resources:
            if results:
                previtem = results[-1]
                if not self.getDebugMode() and \
                   self.compareResources(resource, previtem):
                    res_id = resource.get('id')
                    prev_id = previtem.get('id')
                    self.finalizeResourceMerging(resource, previtem)
                    if self.concatenatedresources.has_key(prev_id):
                        self.concatenatedresources[prev_id].append(res_id)
                    else:
                        magic_id = self.generateId()
                        self.concatenatedresources[magic_id] = [prev_id, res_id]
                        previtem['id'] = magic_id
                else:
                    results.append(resource)
            else:
                results.append(resource)

        resources = self.getResources()
        for resource in resources:
            self.concatenatedresources[resource['id']] = [resource['id']]
        self.cookedresources = tuple(results)

    security.declarePrivate('evaluateExpression')
    def evaluateExpression(self, expression, context):
        """Evaluate an object's TALES condition to see if it should be
        displayed.
        """
        try:
            if expression and context is not None:
                portal = getToolByName(self, 'portal_url').getPortalObject()

                # Find folder (code courtesy of CMFCore.ActionsTool)
                if context is None or not hasattr(context, 'aq_base'):
                    folder = portal
                else:
                    folder = context
                    # Search up the containment hierarchy until we find an
                    # object that claims it's PrincipiaFolderish.
                    while folder is not None:
                        if getattr(aq_base(folder), 'isPrincipiaFolderish', 0):
                            # found it.
                            break
                        else:
                            folder = aq_parent(aq_inner(folder))

                __traceback_info__ = (folder, portal, context, expression)
                ec = createExprContext(folder, portal, context)
                return Expression(expression)(ec)
            else:
                return 1
        except AttributeError:
            return 1

    security.declarePrivate('getResource')
    def getResource(self, item, context):
        """Fetch resource for delivery."""
        ids = self.concatenatedresources.get(item, None)
        if ids is not None:
            ids = ids[:]
        output = ""
        if len(ids) > 1:
            output = output + self.merged_output_prefix
        resources = self.getResourcesDict()

        for id in ids:
            try:
                obj = getattr(context, id)
            except AttributeError, KeyError:
                output += "\n/* XXX ERROR -- could not find '%s'*/\n" % id
                content = ''
                obj = None

            if obj is not None:
                if hasattr(aq_base(obj),'meta_type') and \
                   obj.meta_type in ['DTML Method', 'Filesystem DTML Method']:
                    content = obj(client=self.aq_parent, REQUEST=self.REQUEST,
                                  RESPONSE=self.REQUEST.RESPONSE)
                # We should add more explicit type-matching checks
                elif hasattr(aq_base(obj), 'index_html') and \
                     callable(obj.index_html):
                    content = obj.index_html(self.REQUEST,
                                             self.REQUEST.RESPONSE)
                elif callable(obj):
                    content = obj(self.REQUEST, self.REQUEST.RESPONSE)
                else:
                    content = str(obj)

            # Add start/end notes to the resource for better
            # understanding and debugging
            if content:
                output += '\n/* ----- %s ----- */\n' % (id,)
                output += self.finalizeContent(resources[id], content)
                output += '\n'
        return output

    #
    # ZMI Methods
    #

    security.declareProtected(permissions.ManagePortal, 'moveResourceUp')
    def moveResourceUp(self, id, steps=1, REQUEST=None):
        """Move the resource up 'steps' number of steps."""
        index = self.getResourcePosition(id)
        self.moveResource(id, index - steps)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'moveResourceDown')
    def moveResourceDown(self, id, steps=1, REQUEST=None):
        """Move the resource down 'steps' number of steps."""
        index = self.getResourcePosition(id)
        self.moveResource(id, index + steps)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'moveResourceToTop')
    def moveResourceToTop(self, id, REQUEST=None):
        """Move the resource to the first position."""
        self.moveResource(id, 0)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'moveResourceToBottom')
    def moveResourceToBottom(self, id, REQUEST=None):
        """Move the resource to the last position."""
        self.moveResource(id, len(self.resources))
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'moveResourceBefore')
    def moveResourceBefore(self, id, dest_id, REQUEST=None):
        """Move the resource before the resource with dest_id."""
        index = self.getResourcePosition(id)
        dest_index = self.getResourcePosition(dest_id)
        if index < dest_index:
            self.moveResource(id, dest_index - 1)
        else:
            self.moveResource(id, dest_index)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'moveResourceAfter')
    def moveResourceAfter(self, id, dest_id, REQUEST=None):
        """Move the resource after the resource with dest_id."""
        index = self.getResourcePosition(id)
        dest_index = self.getResourcePosition(dest_id)
        if index < dest_index:
            self.moveResource(id, dest_index)
        else:
            self.moveResource(id, dest_index + 1)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    #
    # Protected Methods
    #

    security.declareProtected(permissions.ManagePortal, 'registerResource')
    def registerResource(self, id, expression='', enabled=True):
        """Register a resource."""
        resource = {}
        resource['id'] = id
        resource['expression'] = expression
        resource['enabled'] = enabled
        self.storeResource(resource)

    security.declareProtected(permissions.ManagePortal, 'unregisterResource')
    def unregisterResource(self, id):
        """Unregister a registered resource."""
        resources = [item for item in self.getResources()
                     if item.get('id') != id]
        self.resources = tuple(resources)
        self.cookResources()

    security.declareProtected(permissions.ManagePortal, 'getResources')
    def getResources(self):
        """Get all the registered resource data, uncooked.

        For management screens.
        """
        return tuple([item.copy() for item in self.resources])

    security.declareProtected(permissions.ManagePortal, 'moveResource')
    def moveResource(self, id, position):
        """Move a registered resource to the given position."""
        index = self.getResourcePosition(id)
        if index == position:
            return
        elif position < 0:
            position = 0
        resources = list(self.getResources())
        resource = resources.pop(index)
        resources.insert(position, resource)
        self.resources = tuple(resources)
        self.cookResources()

    security.declareProtected(permissions.ManagePortal, 'getResourcePosition')
    def getResourcePosition(self, id):
        """Get the position (order) of an resource given its id."""
        resources = list(self.getResources())
        resource_ids = [item.get('id') for item in resources]
        try:
            return resource_ids.index(id)
        except ValueError:
            raise NotFound, 'Resource %s was not found' % str(id)

    security.declareProtected(permissions.ManagePortal, 'getDebugMode')
    def getDebugMode(self):
        """Is resource merging disabled?"""
        try:
            return self.debugmode
        except AttributeError:
            # fallback for old installs. should we even care?
            return False

    security.declareProtected(permissions.ManagePortal, 'setDebugMode')
    def setDebugMode(self, value):
        """Set whether resource merging should be disabled."""
        self.debugmode = value

    security.declareProtected(permissions.View, 'getEvaluatedResources')
    def getEvaluatedResources(self, context):
        """Return the filtered evaluated resources."""
        results = self.cookedresources
        # filter results by expression
        results = [item for item in results
                   if self.evaluateExpression(item.get('expression'), context)]
        return results

    security.declareProtected(permissions.View, 'getInlineResource')
    def getInlineResource(self, item, context):
        """Return a resource as inline code, not as a file object.

        Needs to take care not to mess up http headers.
        """
        headers = self.REQUEST.RESPONSE.headers.copy()
        # Save the RESPONSE headers
        output = self.getResource(item, context)
        # File objects and other might manipulate the headers,
        # something we don't want. we set the saved headers back
        self.REQUEST.RESPONSE.headers = headers
        # This should probably be solved a cleaner way
        return str(output)

    security.declareProtected(permissions.View, 'getContentType')
    def getContentType(self):
        """Return the registry content type.

        Should be overwritten by subclasses.
        """
        return 'text/plain'
