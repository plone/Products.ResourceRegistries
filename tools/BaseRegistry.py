import random

# we *have* to use StringIO here, because we can't add attributes to cStringIO
# instances (needed in BaseRegistryTool.__getitem__).
from StringIO import StringIO

from App.Common import rfc1123_date
from DateTime import DateTime
from zExceptions import NotFound
from Globals import InitializeClass, Persistent, PersistentMapping
from AccessControl import ClassSecurityInfo, Unauthorized

from Acquisition import aq_base, aq_parent, aq_inner, ExplicitAcquisitionWrapper

from OFS.Image import File
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager

from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from Products.ResourceRegistries import config
from Products.ResourceRegistries import permissions
from Products.ResourceRegistries.interfaces import IResourceRegistry


class Resource(Persistent):
    security = ClassSecurityInfo()

    def __init__(self, id, **kwargs):
        self._data = PersistentMapping()
        self._data['id'] = id
        self._data['expression'] = kwargs.get('expression', '')
        self._data['enabled'] = kwargs.get('enabled', True)
        self._data['cookable'] = kwargs.get('cookable', True)

    def copy(self):
        result = self.__class__(self.getId())
        for key, value in self._data.items():
            if key != 'id':
                result._data[key] = value
        return result

    security.declarePublic('getId')
    def getId(self):
        return self._data['id']

    def _setId(self, id):
        self._data['id'] = id

    security.declarePublic('getExpression')
    def getExpression(self):
        return self._data['expression']

    security.declareProtected(permissions.ManagePortal, 'setExpression')
    def setExpression(self, expression):
        self._data['expression'] = expression

    security.declarePublic('getEnabled')
    def getEnabled(self):
        return self._data['enabled']

    security.declareProtected(permissions.ManagePortal, 'setEnabled')
    def setEnabled(self, enabled):
        self._data['enabled'] = enabled

    security.declarePublic('getCookable')
    def getCookable(self):
        return self._data['cookable']

    security.declareProtected(permissions.ManagePortal, 'setCookable')
    def setCookable(self, cookable):
        self._data['cookable'] = cookable

InitializeClass(Resource)


class BaseRegistryTool(UniqueObject, SimpleItem, PropertyManager):
    """Base class for a Plone registry managing resource files."""

    security = ClassSecurityInfo()
    __implements__ = (SimpleItem.__implements__, IResourceRegistry)
    manage_options = SimpleItem.manage_options

    attributes_to_compare = ('getExpression', 'getCookable')
    filename_base = 'ploneResources'
    filename_appendix = '.res'
    merged_output_prefix = ''
    cache_duration = 3600
    resource_class = Resource

    #
    # Private Methods
    #

    def __init__(self):
        """Add the storages."""
        self.resources = ()
        self.cookedresources = ()
        self.concatenatedresources = {}
        self.debugmode = False

    def __getitem__(self, item):
        """Return a resource from the registry."""
        output = self.getResourceContent(item, self)
        if self.getDebugMode():
            duration = 0
        else:
            duration = self.cache_duration  # duration in seconds
        seconds = float(duration)*24.0*3600.0
        response = self.REQUEST.RESPONSE
        response.setHeader('Expires',rfc1123_date((DateTime() + duration).timeTime()))
        response.setHeader('Cache-Control', 'max-age=%d' % int(seconds))
        contenttype = self.getContentType()
        # make output file like and add an headers dict, so the contenttype
        # is properly set in the headers
        output = StringIO(output)
        output.headers = {}
        output.headers['content-type'] = contenttype
        return File(item, item, output).__of__(self)

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
            if sheet.getId() == id:
                raise ValueError, 'Duplicate id %s' %(id)

    security.declarePrivate('storeResource')
    def storeResource(self, resource):
        """Store a resource."""
        self.validateId(resource.getId(), self.getResources())
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
            d[s.getId()] = s
        return d

    security.declarePrivate('compareResources')
    def compareResources(self, s1, s2):
        """Check if two resources are compatible."""
        for attr in self.attributes_to_compare:
            if getattr(s1, attr)() != getattr(s2, attr)():
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

    security.declareProtected(permissions.ManagePortal, 'cookResources')
    def cookResources(self):
        """Cook the stored resources."""
        resources = [r.copy() for r in self.getResources() if r.getEnabled()]
        self.concatenatedresources = {}
        self.cookedresources = ()
        results = []
        for resource in resources:
            if results:
                previtem = results[-1]
                if not self.getDebugMode() and \
                   self.compareResources(resource, previtem):
                    res_id = resource.getId()
                    prev_id = previtem.getId()
                    self.finalizeResourceMerging(resource, previtem)
                    if self.concatenatedresources.has_key(prev_id):
                        self.concatenatedresources[prev_id].append(res_id)
                    else:
                        magic_id = self.generateId()
                        self.concatenatedresources[magic_id] = [prev_id, res_id]
                        previtem._setId(magic_id)
                else:
                    results.append(resource)
            else:
                results.append(resource)

        resources = self.getResources()
        for resource in resources:
            self.concatenatedresources[resource.getId()] = [resource.getId()]
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

    security.declareProtected(permissions.ManagePortal, 'registerStylesheet')
    def getResource(self, id):
        """Get resource object by id.
        
        If any property of the resource is changed, then cookResources of the
        registry must be called."""
        resources = self.getResourcesDict()
        return ExplicitAcquisitionWrapper(resources.get(id, None), self)

    security.declarePrivate('getResourceContent')
    def getResourceContent(self, item, context):
        """Fetch resource content for delivery."""
        ids = self.concatenatedresources.get(item, None)
        resources = self.getResourcesDict()
        if ids is not None:
            ids = ids[:]
        output = ""
        if len(ids) > 1:
            output = output + self.merged_output_prefix

        portal = None
        u_tool = getToolByName(self, 'portal_url', None)
        if u_tool:
            portal = u_tool.getPortalObject()

        if context == self and portal is not None:
            context = portal

        for id in ids:
            try:
                if portal is not None:
                    obj = context.restrictedTraverse(id)
                else:
                    #Can't do anything other than attempt a getattr
                    obj = getattr(context, id)
            except (AttributeError, KeyError):
                output += "\n/* XXX ERROR -- could not find '%s'*/\n" % id
                content = ''
                obj = None
            except Unauthorized:
                #If we're just returning a single resource, raise an Unauthorized,
                #otherwise we're merging resources in which case just log an error
                if len(ids) > 1:
                    #Object probably isn't published yet
                    output += "\n/* XXX ERROR -- access to '%s' not authorized */\n" % id
                    content = ''
                    obj = None
                else:
                    raise

            if obj is not None:
                if hasattr(aq_base(obj),'meta_type') and  obj.meta_type in ['DTML Method', 'Filesystem DTML Method']:
                    content = obj(client=self.aq_parent, REQUEST=self.REQUEST,
                                  RESPONSE=self.REQUEST.RESPONSE)
                
                elif hasattr(aq_base(obj),'meta_type') and obj.meta_type == 'Filesystem File':
                   obj._updateFromFS()
                   content = obj._readFile(0)
                elif hasattr(aq_base(obj),'meta_type') and obj.meta_type == 'ATFile':
                    content = str(obj)
                # We should add more explicit type-matching checks
                elif hasattr(aq_base(obj), 'index_html') and callable(obj.index_html):
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
    def registerResource(self, id, expression='', enabled=True, cookable=True):
        """Register a resource."""
        resource = Resource(id,
                            expression=expression,
                            enabled=enabled,
                            cookable=cookable)
        self.storeResource(resource)

    security.declareProtected(permissions.ManagePortal, 'unregisterResource')
    def unregisterResource(self, id):
        """Unregister a registered resource."""
        resources = [item for item in self.getResources()
                     if item.getId() != id]
        self.resources = tuple(resources)
        self.cookResources()

    security.declareProtected(permissions.ManagePortal, 'renameResource')
    def renameResource(self, old_id, new_id):
        """Change the id of a registered resource."""
        self.validateId(new_id, self.getResources())
        resources = list(self.resources)
        for resource in resources:
            if resource.getId() == old_id:
                resource._setId(new_id)
                break
        self.resources = tuple(resources)
        self.cookResources()

    security.declareProtected(permissions.ManagePortal, 'getResourceIds')
    def getResourceIds(self):
        """Return the ids of all resources."""
        return tuple([x.getId() for x in self.getResources()])

    security.declareProtected(permissions.ManagePortal, 'getResources')
    def getResources(self):
        """Get all the registered resource data, uncooked.

        For management screens.
        """
        result = []
        for item in self.resources:
            if isinstance(item, dict):
                # BBB we used dicts before
                item = item.copy()
                item_id = item['id']
                del item['id']
                obj = self.resource_class(item_id, **item)
                result.append(obj)
            else:
                result.append(item)
        return tuple(result)

    security.declareProtected(permissions.ManagePortal, 'getCookedResources')
    def getCookedResources(self):
        """Get the cooked resource data."""
        result = []
        for item in self.cookedresources:
            if isinstance(item, dict):
                # BBB we used dicts before
                item = item.copy()
                item_id = item['id']
                del item['id']
                obj = self.resource_class(item_id, **item)
                result.append(obj)
            else:
                result.append(item)
        return tuple(result)

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
        resource_ids = list(self.getResourceIds())
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
        results = self.getCookedResources()

        # filter results by expression
        results = [item for item in results
                   if self.evaluateExpression(item.getExpression(), context)]

        # filter out resources to which the user does not have access
        # this is mainly cosmetic but saves raising lots of Unauthorized
        # requests whilst resources are in their private state. 404s should stay
        # though since they indicate an error on the part of the designer/developer
        # or are considered legal by the Unit Tests!
        portal = None
        u_tool = getToolByName(self, 'portal_url', None)
        if u_tool:
            portal = u_tool.getPortalObject()

        if portal is not None:
            #If we don't have a portal object, just let'em through - the stylesheets will raise
            # an Unauthorized when requested though
            for item in results:
                id = item.getId()
                if not id.startswith(self.filename_base):
                    try:
                        obj = portal.restrictedTraverse(id)
                    except Unauthorized:
                        #Only include links to Unauthorized objects if we're debugging
                        if not self.getDebugMode():
                            results.remove(item)
                    except (AttributeError, KeyError):
                        pass

        return results

    security.declareProtected(permissions.View, 'getInlineResource')
    def getInlineResource(self, item, context):
        """Return a resource as inline code, not as a file object.

        Needs to take care not to mess up http headers.
        """
        headers = self.REQUEST.RESPONSE.headers.copy()
        # Save the RESPONSE headers
        output = self.getResourceContent(item, context)
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
