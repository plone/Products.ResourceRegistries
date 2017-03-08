import logging

# we *have* to use StringIO here, because we can't add attributes to cStringIO
# instances (needed in BaseRegistryTool.__getitem__).
from StringIO import StringIO
from urllib import quote_plus
from hashlib import md5
from time import time

from zope.interface import implements, alsoProvides
from zope.component import getAdapters
from zope.component import queryUtility
from zope.site.hooks import getSite

from plone.registry.interfaces import IRegistry

from AccessControl import ClassSecurityInfo, Unauthorized
from AccessControl.SecurityManagement import getSecurityManager
import Acquisition
from Acquisition import aq_base, aq_parent, aq_inner, ExplicitAcquisitionWrapper
from App.class_init import InitializeClass
from App.Common import rfc1123_date
from DateTime import DateTime
from Persistence import Persistent
from Persistence import PersistentMapping
from OFS.Image import File
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager
from OFS.Cache import Cacheable
from ZPublisher.Iterators import IStreamIterator

from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.Five.browser.resource import Resource as z3_Resource

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.ResourceRegistries import permissions
from Products.ResourceRegistries import config

from Products.ResourceRegistries.interfaces import IResourceRegistry
from Products.ResourceRegistries.interfaces import ICookedFile
from Products.ResourceRegistries.interfaces import IResourceProvider
from Products.ResourceRegistries.interfaces.settings import IResourceRegistriesSettings

DEVEL_MODE = dict()

LOGGER = logging.getLogger('ResourceRegistries')

def getDummyFileForContent(name, ctype):
    # make output file like and add an headers dict, so the contenttype
    # is properly set in the headers
    output = StringIO()
    output.headers = {'content-type': ctype}
    file_ = File(name, name, output)
    alsoProvides(file_, ICookedFile)
    return file_

def getCharsetFromContentType(contenttype, default='utf-8'):
    contenttype = contenttype.lower()
    if 'charset=' in contenttype:
        i = contenttype.index('charset=')
        charset = contenttype[i+8:]
        charset = charset.split(';')[0]
        return charset
    else:
        return default

def is_anonymous():
    user = getSecurityManager().getUser()
    return bool(user.getUserName() == 'Anonymous User')

class PersistentResourceProvider(object):
    implements(IResourceProvider)

    def __init__(self, context):
        self.context = context

    def getResources(self):
        """Get a list of available Resource objects
        """
        return self.context.resources

def cookWhenChangingSettings(settings, event):
    """When our settings are changed, re-cook the main registries
    """
    for name in (config.JSTOOLNAME, config.CSSTOOLNAME, config.KSSTOOLNAME,):
        tool = getToolByName(getSite(), name, None)
        if tool is not None:
            tool.cookResources()

class Resource(Persistent):
    security = ClassSecurityInfo()

    def __init__(self, id, **kwargs):
        self._data = PersistentMapping()
        extres = id.startswith('http://') or id.startswith('https://') or id.startswith('//')
        if not extres and (id.startswith('/') or id.endswith('/') or ('//' in id)):
            raise ValueError("Invalid Resource ID: %s" % id)
        self._data['id'] = id
        expression = kwargs.get('expression', '')
        self.setExpression(expression)
        self._data['authenticated'] = kwargs.get('authenticated', False)
        self._data['enabled'] = kwargs.get('enabled', True)
        self._data['cookable'] = kwargs.get('cookable', True)
        self._data['cacheable'] = kwargs.get('cacheable', True)
        self._data['conditionalcomment'] = kwargs.get('conditionalcomment','')
        self._data['bundle'] = kwargs.get('bundle', 'default')
        self.isExternal = extres
        if extres:
            self._data['cacheable'] = False #External resources are NOT cacheable
            self._data['cookable'] = False #External resources are NOT mergable

    def copy(self):
        result = self.__class__(self.getId())
        for key, value in self._data.items():
            if key != 'id':
                result._data[key] = value
        return result

    security.declarePublic('getId')
    def getId(self):
        return self._data['id']

    security.declarePublic('getQuotedId')
    def getQuotedId(self):
        return quote_plus(self._data['id'])

    security.declareProtected(permissions.ManagePortal, '_setId')
    def _setId(self, id):
        extres = id.startswith('http://') or id.startswith('https://') or id.startswith('//')
        if not extres and (id.startswith('/') or id.endswith('/') or ('//' in id)):
            raise ValueError("Invalid Resource ID: %s" %id)
        self._data['id'] = id

    security.declarePublic('getCookedExpression')
    def getCookedExpression(self):
        # Automatic inline migration of expressions
        if 'cooked_expression' not in self._data:
            expr = Expression(self._data['expression'])
            self._data['cooked_expression'] = expr
        return self._data['cooked_expression']

    security.declarePublic('getExpression')
    def getExpression(self):
        return self._data['expression']

    security.declareProtected(permissions.ManagePortal, 'setExpression')
    def setExpression(self, expression):
        # Update the cooked expression
        self._data['cooked_expression'] = Expression( expression )
        self._data['expression'] = expression

    security.declarePublic('getAuthenticated')
    def getAuthenticated(self):
        # Automatic inline migration
        if 'authenticated' not in self._data:
            self._data['authenticated'] = False
        return bool(self._data['authenticated'])

    security.declareProtected(permissions.ManagePortal, 'setAuthenticated')
    def setAuthenticated(self, authenticated):
        self._data['authenticated'] = authenticated

    security.declarePublic('getEnabled')
    def getEnabled(self):
        return bool(self._data['enabled'])

    security.declareProtected(permissions.ManagePortal, 'setEnabled')
    def setEnabled(self, enabled):
        self._data['enabled'] = enabled

    security.declarePublic('getCookable')
    def getCookable(self):
        return self._data['cookable']

    security.declareProtected(permissions.ManagePortal, 'setCookable')
    def setCookable(self, cookable):
        if self.isExternalResource() and cookable:
            raise ValueError("External Resources cannot be merged")
        self._data['cookable'] = cookable

    security.declarePublic('getCacheable')
    def getCacheable(self):
        # as this is a new property, old instance might not have that value, so
        # return True as default
        return self._data.get('cacheable', True)

    security.declareProtected(permissions.ManagePortal, 'setCacheable')
    def setCacheable(self, cacheable):
        if self.isExternalResource() and cacheable:
            raise ValueError("External Resources are not cacheable")
        self._data['cacheable'] = cacheable

    security.declarePublic('getConditionalcomment')
    def getConditionalcomment(self):
        # New property, return blank if the old instance doesn't have that value
        return self._data.get('conditionalcomment','')

    security.declareProtected(permissions.ManagePortal, 'setConditionalcomment')
    def setConditionalcomment(self, conditionalcomment):
        self._data['conditionalcomment'] = conditionalcomment

    security.declarePublic('isExternalResource')
    def isExternalResource(self):
        return getattr(self, 'isExternal', False)

    security.declarePublic('getBundle')
    def getBundle(self):
        return self._data.get('bundle', None) or 'default'

    security.declareProtected(permissions.ManagePortal, 'setBundle')
    def setBundle(self, bundle):
        self._data['bundle'] = bundle

InitializeClass(Resource)


class Skin(Acquisition.Implicit):
    security = ClassSecurityInfo()

    def __init__(self, skin, resources):
        self._skin = skin
        self.resources = resources

    def __before_publishing_traverse__(self, object, REQUEST):
        """ Pre-traversal hook. Specify the skin.
        """
        self.changeSkin(self._skin, REQUEST)

    def __bobo_traverse__(self, REQUEST, name):
        """Traversal hook."""
        if REQUEST is not None and self.resources.get(name, None) is not None:
            parent = aq_parent(self)
            # see BaseTool.__bobo_traverse__
            deferred = getDummyFileForContent(name, self.getContentType())
            post_traverse = getattr(aq_base(REQUEST), 'post_traverse', None)
            if post_traverse is not None:
                post_traverse(parent.deferredGetContent, (deferred, name, self._skin))
            else:
                parent.deferredGetContent(deferred, name, self._skin)
            return deferred.__of__(parent)
        obj = getattr(self, name, None)
        if obj is not None:
            return obj
        raise AttributeError('%s' % (name,))

InitializeClass(Skin)

_marker = {} # must be a dict

class BaseRegistryTool(UniqueObject, SimpleItem, PropertyManager, Cacheable):
    """Base class for a Plone registry managing resource files."""

    security = ClassSecurityInfo()
    implements(IResourceRegistry)

    manage_bundlesForm = PageTemplateFile('www/bundles', config.GLOBALS)

    manage_options = (
        {
            'label': 'Bundles',
            'action': 'manage_bundlesForm',
        },
    ) + SimpleItem.manage_options

    attributes_to_compare = ('getAuthenticated', 'getExpression',
                             'getCookable', 'getCacheable',
                             'getConditionalcomment')
    filename_base = 'ploneResources'
    filename_appendix = '.res'
    merged_output_prefix = u''
    # cache life in days (note: value can be a float)
    cache_duration = 3600
    resource_class = Resource

    # Kept here for BBB to avoid need to migrate these in
    cookedResourcesByTheme = _marker
    concatenatedResourcesByTheme = _marker

    #
    # Private Methods
    #

    def __init__(self):
        """Add the storages."""
        self.resources = ()

        self.cookedResourcesByTheme = {} # theme -> tuple of cooked resources
        self.concatenatedResourcesByTheme = {} # theme -> {magic (public) id -> list of actual resource ids}

    # Get/set cooked resources and concatenated resources for the current
    # theme. This is mainly BBB support.

    @property
    def cookedresources(self):
        if 'cookedresources' in self.__dict__:
            self._migrateCookedResouces()
        theme = self.getCurrentSkinName()
        return self.cookedResourcesByTheme.get(theme, ())

    @property
    def concatenatedresources(self):
        if 'concatenatedresources' in self.__dict__:
            self._migrateCookedResouces()
        theme = self.getCurrentSkinName()
        return self.concatenatedResourcesByTheme.get(theme, {})

    def _migrateCookedResouces(self):
        LOGGER.warn("Migrating old concatenated resources storage on the fly - this should only happen once per tool")
        del self.__dict__['cookedresources']
        del self.__dict__['concatenatedresources']
        self.cookResources()  # Cook after deleting to avoid recursive call.

    def __getitem__(self, item):
        """Return a resource from the registry."""
        original = self.REQUEST.get('original', False)
        output = self.getResourceContent(item, self, original)
        contenttype = self.getContentType()
        return (output, contenttype)

    def deferredGetContent(self, deferred, name, skin=None):
        """ uploads data of a resource to deferred """
        # "deferred" was previosly created by a getDummyFileForContent
        # call in the __bobo_traverse__ method. As the name suggests,
        # the file is merely a traversable dummy with appropriate
        # headers and name. Now as soon as REQUEST.traverse
        # finishes and gets to the part where it calls the tuples
        # register using post_traverse (that's actually happening
        # right now) we can be sure, that all necessary security
        # stuff has taken place (e.g. authentication).
        kw = {'skin':skin,'name':name}
        data = None
        duration = self.cache_duration  # duration in seconds
        if not self.getDebugMode() and self.isCacheable(name):
            if self.ZCacheable_isCachingEnabled():
                data = self.ZCacheable_get(keywords=kw)
            if data is None:
                # This is the part were we would fail if
                # we would just return the ressource
                # without using the post_traverse hook:
                # self.__getitem__ leads (indirectly) to
                # a restrictedTraverse call which performs
                # security checks. So if a tool (or its ressource)
                # is not "View"able by anonymous - we'd
                # get an Unauthorized exception.
                data = self.__getitem__(name)
                self.ZCacheable_set(data, keywords=kw)
        else:
            data = self.__getitem__(name)
            duration = 0

        output, contenttype = data

        seconds = float(duration)*24.0*3600.0
        response = self.REQUEST.RESPONSE
        response.setHeader('Expires',rfc1123_date((DateTime() + duration).timeTime()))
        response.setHeader('Cache-Control', 'max-age=%d' % int(seconds))

        if isinstance(output, unicode):
            output = output.encode('utf-8')
            if 'charset=' not in contenttype:
                contenttype += ';charset=utf-8'

        # At this point we are ready to provide some content
        # for our dummy and since it's just a File instance,
        # we can "upload" (a quite delusive method name) the
        # data and that's it.
        deferred.update_data(output, content_type=contenttype)

    def __bobo_traverse__(self, REQUEST, name):
        """Traversal hook."""

        # First see if it is a skin
        skintool = getToolByName(self, 'portal_skins')
        skins = skintool.getSkinSelections()
        if name in skins:
            return Skin(name, self.concatenatedResourcesByTheme.get(name, {})).__of__(self)

        theme = self.getCurrentSkinName()

        if REQUEST is not None and \
                self.concatenatedResourcesByTheme.get(theme, {}).get(name, None) is not None:
            # __bobo_traverse__ is called before the authentication has
            # taken place, so if some operations require an authenticated
            # user (like restrictedTraverse in __getitem__) it will fail.
            # Now we can circumvent that by using the post_traverse()
            # method from BaseRequest. It temporarely stores a callable
            # along with its arguments in a REQUEST instance and calls
            # them at the end of BaseRequest.traverse()
            deferred = getDummyFileForContent(name, self.getContentType())
            # __bobo_traverse__ might be called from within
            # OFS.Traversable.Traversable.unrestrictedTraverse()
            # which passes a simple dict to the method, instead
            # of a "real" REQUEST object
            post_traverse = getattr(aq_base(REQUEST), 'post_traverse', None)
            if post_traverse is not None:
                post_traverse(self.deferredGetContent, (deferred, name, None))
            else:
                self.deferredGetContent(deferred, name, None)
            return deferred.__of__(self)
        obj = getattr(self, name, None)
        if obj is not None:
            return obj
        raise AttributeError('%s' % (name,))

    security.declarePublic('isCacheable')
    def isCacheable(self, name, theme=None):
        """Return a boolean whether the resource is cacheable or not."""

        if theme is None:
            theme = self.getCurrentSkinName()

        resource_id = self.concatenatedResourcesByTheme.get(theme, {}).get(name, [None])[0]
        if resource_id is None:
            return False
        resources = self.getResourcesDict()
        resource = resources.get(resource_id, None)
        result = resource.getCacheable()
        return result

    security.declarePrivate('validateId')
    def validateId(self, id, existing):
        """Safeguard against duplicate ids."""
        for sheet in existing:
            if sheet.getId() == id:
                raise ValueError('Duplicate id %s' %(id))

    security.declarePrivate('storeResource')
    def storeResource(self, resource, skipCooking=False):
        """Store a resource."""
        self.validateId(resource.getId(), self.resources)
        resources = list(self.resources)
        resources.append(resource)
        self.resources = tuple(resources)
        if not skipCooking:
            self.cookResources()

    security.declarePrivate('clearResources')
    def clearResources(self):
        """Clears all resource data.

        Convenience funtion for Plone migrations and tests.
        """
        self.resources = ()
        self.cookedResourcesByTheme = {}
        self.concatenatedResourcesByTheme = {}

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
        if s1.isExternalResource() or s2.isExternalResource():
            return False
        for attr in self.attributes_to_compare:
            if getattr(s1, attr)() != getattr(s2, attr)():
                return False
        return True

    security.declarePrivate('sortResources')
    def sortResourceKey(self, resource):
        """Returns a sort key for the resource."""
        return [getattr(resource, attr)() for attr in
                self.attributes_to_compare]

    security.declarePrivate('generateId')
    def generateId(self, resource, other=None):
        """Generate a random id."""

        res_id = resource.getId()

        if other is not None:
            other_id = other.getId()
            key = md5(other_id)
            key.update(res_id)
            base = res_id.rsplit('-')[0]
            key = "%s-" % (base, key.hexdigest())
            ext = "." + res_id.rsplit('.', 1)[1]
        else:
            base = res_id.replace('++', '').replace('/', '').rsplit('.', 1)[0]
            key = md5(res_id)
            key.update(str(int(time() * 1000)))
            key = "%s-cachekey-%s" % (base, key.hexdigest())
            ext = self.filename_appendix

        return key + ext

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
        if self.ZCacheable_isCachingEnabled():
            self.ZCacheable_invalidate()

        self.concatenatedResourcesByTheme = {}
        self.cookedResourcesByTheme = {}

        bundlesForThemes = self.getBundlesForThemes()
        for theme, bundles in bundlesForThemes.items():

            resources = [r.copy() for r in self.getResources() if r.getEnabled()]
            results = []

            concatenatedResources = self.concatenatedResourcesByTheme[theme] = {}

            for resource in resources:

                # Skip resources in bundles not in this theme. None bundles
                # are assumed to

                bundle = resource.getBundle()
                if bundle not in bundles:
                    continue

                if results:
                    previtem = results[-1]

                    # Is this resource compatible the previous one we used?
                    if resource.getCookable() and previtem.getCookable() \
                           and self.compareResources(resource, previtem):
                        res_id = resource.getId()
                        prev_id = previtem.getId()
                        self.finalizeResourceMerging(resource, previtem)

                        # Add the original id under concatenated resources or
                        # create a new one starting with the previous item
                        if concatenatedResources.has_key(prev_id):
                            concatenatedResources[prev_id].append(res_id)
                        else:
                            magic_id = self.generateId(resource, previtem)
                            concatenatedResources[magic_id] = [prev_id, res_id]
                            previtem._setId(magic_id)

                    else:
                        if resource.getCookable() or resource.getCacheable():
                            magic_id = self.generateId(resource)
                            concatenatedResources[magic_id] = [resource.getId()]
                            resource._setId(magic_id)
                        results.append(resource)
                else: # No resources collated yet

                    # If cookable or cacheable, generate a magic id, change
                    # the resource id to be this id, and record the old id in the
                    # list of ids for this magic id under concatenated resources
                    if resource.getCookable() or resource.getCacheable():
                        magic_id = self.generateId(resource)
                        concatenatedResources[magic_id] = [resource.getId()]
                        resource._setId(magic_id)
                    results.append(resource)

            # Get the raw list of resources and store these as well in
            # concatenated resources
            resources = self.getResources()
            for resource in resources:
                concatenatedResources[resource.getId()] = [resource.getId()]

            self.cookedResourcesByTheme[theme] = tuple(results)

    security.declarePrivate('evaluate')
    def evaluate(self, item, context):
        """Evaluate an object to see if it should be displayed.
        """
        if item.getAuthenticated():
            if is_anonymous():
                return False
            else:
                return True
        if not item.getExpression():
            return True
        return self.evaluateExpression(item.getCookedExpression(), context)

    security.declarePrivate('evaluateExpression')
    def evaluateExpression(self, expression, context):
        """Evaluate an object's TALES condition to see if it should be
        displayed.
        """
        try:
            if expression.text and context is not None:
                portal = getToolByName(context, 'portal_url').getPortalObject()

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
                # add 'context' as an alias for 'object'
                ec.setGlobal('context', context)
                return expression(ec)
            else:
                return True
        except AttributeError:
            return True

    security.declareProtected(permissions.ManagePortal, 'getResource')
    def getResource(self, id):
        """Get resource object by id.

        If any property of the resource is changed, then cookResources of the
        registry must be called."""
        resources = self.getResourcesDict()
        resource = resources.get(id, None)
        if resource is not None:
            return ExplicitAcquisitionWrapper(resource, self)
        return None

    security.declarePrivate('getResourceContent')
    def getResourceContent(self, item, context, original=False, theme=None):
        """Fetch resource content for delivery."""

        if theme is None:
            theme = self.getCurrentSkinName()

        ids = self.concatenatedResourcesByTheme.get(theme, {}).get(item, None)
        resources = self.getResourcesDict()
        if ids is not None:
            ids = ids[:]
        output = u""
        if len(ids) > 1:
            output = output + self.merged_output_prefix

        portal = getToolByName(context, 'portal_url').getPortalObject()

        if context == self and portal is not None:
            context = portal

        default_charset = 'utf-8'

        for id in ids:
            # skip external resources that look like //netdna.bootstrapcdn.com/etc...
            if id[0:2] == '//':
                continue
            try:
                if portal is not None:
                    obj = context.restrictedTraverse(id)
                else:
                    #Can't do anything other than attempt a getattr
                    obj = getattr(context, id)
            except (AttributeError, KeyError):
                output += u"\n/* XXX ERROR -- could not find '%s'*/\n" % id
                content = u''
                obj = None
            except Unauthorized:
                #If we're just returning a single resource, raise an Unauthorized,
                #otherwise we're merging resources in which case just log an error
                if len(ids) > 1:
                    #Object probably isn't published yet
                    output += u"\n/* XXX ERROR -- access to '%s' not authorized */\n" % id
                    content = u''
                    obj = None
                else:
                    raise

            if obj is not None:
                if isinstance(obj, z3_Resource):
                    # z3 resources
                    # XXX this is a temporary solution, we wrap the five resources
                    # into our mechanism, where it should be the other way around.
                    #
                    # First thing we must be aware of: resources give a complete
                    # response so first we must save the headers.
                    # Especially, we must delete the If-Modified-Since, because
                    # otherwise we might get a 30x response status in some cases.
                    original_headers, if_modified = self._removeCachingHeaders()
                    # Now, get the content.
                    try:
                        method = obj.__browser_default__(self.REQUEST)[1][0]
                    except AttributeError: # zope.app.publisher.browser.fileresource
                        try:
                            method = obj.browserDefault(self.REQUEST)[1][0]
                        except (AttributeError, IndexError):
                            try:
                                method = obj.browserDefault(self.REQUEST)[0].__name__
                            except AttributeError:
                                # The above can all fail if request.method is
                                # POST.  We can still at least try to use the
                                # GET method, as we prefer that anyway.
                                method = getattr(obj, 'GET').__name__
                    method = method in ('HEAD','POST') and 'GET' or method
                    content = getattr(obj, method)()
                    if not isinstance(content, unicode):
                        contenttype = self.REQUEST.RESPONSE.headers.get('content-type', '')
                        contenttype = getCharsetFromContentType(contenttype, default_charset)
                        content = unicode(content, contenttype)
                    self._restoreCachingHeaders(original_headers, if_modified)
                elif hasattr(aq_base(obj),'meta_type') and  obj.meta_type in ['DTML Method', 'Filesystem DTML Method']:
                    content = obj(client=self.aq_parent, REQUEST=self.REQUEST,
                                  RESPONSE=self.REQUEST.RESPONSE)
                    contenttype = self.REQUEST.RESPONSE.headers.get('content-type', '')
                    contenttype = getCharsetFromContentType(contenttype, default_charset)
                    content = unicode(content, contenttype)
                elif hasattr(aq_base(obj),'meta_type') and obj.meta_type == 'Filesystem File':
                    obj._updateFromFS()
                    content = obj._readFile(0)
                    contenttype = getCharsetFromContentType(obj.content_type, default_charset)
                    content = unicode(content, contenttype)
                elif hasattr(aq_base(obj),'meta_type') and obj.meta_type in ('ATFile', 'ATBlob'):
                    f = obj.getFile()
                    contenttype = getCharsetFromContentType(f.getContentType(), default_charset)
                    content = unicode(str(f), contenttype)
                # We should add more explicit type-matching checks
                elif hasattr(aq_base(obj), 'index_html') and callable(obj.index_html):
                    original_headers, if_modified = self._removeCachingHeaders()
                    # "index_html" may use "RESPONSE.write" (e.g. for OFS.Image.Pdata)
                    tmp = StringIO()
                    response_write = self.REQUEST.RESPONSE.write
                    self.REQUEST.RESPONSE.write = tmp.write
                    try:
                        content = obj.index_html(self.REQUEST,
                                                 self.REQUEST.RESPONSE)
                    finally:
                        self.REQUEST.RESPONSE.write = response_write
                    content = tmp.getvalue() or content
                    if not isinstance(content, unicode):
                        content = unicode(content, default_charset)
                    self._restoreCachingHeaders(original_headers, if_modified)
                elif callable(obj):
                    try:
                        content = obj(self.REQUEST, self.REQUEST.RESPONSE)
                    except TypeError:
                        # Could be a view or browser resource
                        content = obj()

                    if IStreamIterator.providedBy(content):
                        content = content.read()

                    if not isinstance(content, unicode):
                        content = unicode(content, default_charset)
                else:
                    content = str(obj)
                    content = unicode(content, default_charset)

            # Add start/end notes to the resource for better
            # understanding and debugging
            if content:
                output += u'\n/* - %s - */\n' % (id,)
                if original:
                    output += content
                else:
                    output += self.finalizeContent(resources[id], content)
                output += u'\n'
        return output

    def _removeCachingHeaders(self):
        orig_response_headers = self.REQUEST.RESPONSE.headers.copy()
        if_modif = self.REQUEST.get_header('If-Modified-Since', None)
        try:
            del self.REQUEST.environ['IF_MODIFIED_SINCE']
        except KeyError:
            pass
        try:
            del self.REQUEST.environ['HTTP_IF_MODIFIED_SINCE']
        except KeyError:
            pass
        return orig_response_headers, if_modif

    def _restoreCachingHeaders(self, original_response_headers, if_modified):
        # Now restore the headers and for safety, check that we
        # have a 20x response. If not, we have a problem and
        # some browser would hang indefinitely at this point.
        if int(self.REQUEST.RESPONSE.getStatus()) / 100 != 2:
            return
        self.REQUEST.environ['HTTP_IF_MODIFIED_SINCE'] = if_modified
        self.REQUEST.RESPONSE.headers = original_response_headers


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
        if dest_index == -1:
            self.moveResourceToTop(id)
        elif index < dest_index:
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
        if dest_index == -1:
            self.moveResourceToBottom(id)
        elif index < dest_index:
            self.moveResource(id, dest_index)
        else:
            self.moveResource(id, dest_index + 1)
        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(permissions.ManagePortal, 'getBundlesForThemes')
    def getBundlesForThemes(self):
        """Get the mapping of theme names to lists of bundles
        """

        mappings = {}

        registry = queryUtility(IRegistry)
        if registry is not None:
            mappings = registry.forInterface(IResourceRegistriesSettings, False).resourceBundlesForThemes or {}
            mappings = dict(mappings) # clone as builtin dict, even if non-builtin dict

        if '(default)' in mappings:
            default = mappings['(default)']
        else:
            default = ['default']

        portal_skins = getToolByName(self, 'portal_skins')
        for theme in portal_skins.getSkinSelections():
            if not theme in mappings:
                mappings[theme] = default

        return mappings

    security.declareProtected(permissions.ManagePortal, 'getBundlesForTheme')
    def getBundlesForTheme(self, theme=None):
        """Get the bundles for a particular theme (defaults to the current)
        """

        if theme is None:
            theme = self.getCurrentSkinName()

        return self.getBundlesForThemes().get(theme, ['default'])

    security.declareProtected(permissions.ManagePortal, 'manage_saveBundlesForThemes')
    def manage_saveBundlesForThemes(self, mappings={}, REQUEST=None):
        """Save theme -> bundle mappings
        """
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IResourceRegistriesSettings)

        m = {}
        for k,v in mappings.items():
            m[str(k)] = [str(x) for x in v if x]
        settings.resourceBundlesForThemes = m

        self.cookResources()

        if REQUEST:
            REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    #
    # Protected Methods
    #

    security.declareProtected(permissions.ManagePortal, 'registerResource')
    def registerResource(self, id, expression='', enabled=True,
                         cookable=True, cacheable=True, conditionalcomment='',
                         authenticated=False, bundle='default'):
        """Register a resource."""
        resource = self.resource_class(
                            id,
                            expression=expression,
                            enabled=enabled,
                            cookable=cookable,
                            cacheable=cacheable,
                            conditionalcomment=conditionalcomment,
                            authenticated=authenticated,
                            bundle=bundle)
        self.storeResource(resource)

    security.declareProtected(permissions.ManagePortal, 'unregisterResource')
    def unregisterResource(self, id):
        """Unregister a registered resource."""
        resources = [item for item in self.resources
                     if item.getId() != id]
        self.resources = tuple(resources)
        self.cookResources()

    security.declareProtected(permissions.ManagePortal, 'renameResource')
    def renameResource(self, old_id, new_id):
        """Change the id of a registered resource."""
        self.validateId(new_id, self.resources)
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
        return tuple([x.getId() for x in self.resources])

    security.declareProtected(permissions.ManagePortal, 'getResources')
    def getResources(self):
        """Get all the registered resource data, uncooked.

        For management screens.
        """
        result = []

        for name, provider in getAdapters((self,), IResourceProvider):
            for item in provider.getResources():
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
    def getCookedResources(self, theme=None):
        """Get the cooked resource data."""
        result = []

        if theme is None:
            theme = self.getCurrentSkinName()

        # If we don't recognise the theme, pretend we're the default one
        bundlesForThemes = self.getBundlesForThemes()

        if self.cookedResourcesByTheme is _marker:
            self._migrateCookedResouces()

        if theme not in bundlesForThemes or theme not in self.cookedResourcesByTheme:
            portal_skins = getToolByName(self, 'portal_skins')
            theme = portal_skins.getDefaultSkin()

        if self.getDebugMode():
            bundles = bundlesForThemes.get(theme, ['default'])
            result = [r.copy() for r in self.getResources() \
                            if r.getEnabled() and (not r.getBundle() or r.getBundle() in bundles)]
        else:
            result = [x for x in self.cookedResourcesByTheme.get(theme, ())]
        return tuple(result)

    security.declareProtected(permissions.ManagePortal, 'moveResource')
    def moveResource(self, id, position):
        """Move a registered resource to the given position."""
        index = self.getResourcePosition(id)
        if index == position:
            return
        elif position < 0:
            position = 0
        resources = list(self.resources)
        resource = resources.pop(index)
        resources.insert(position, resource)
        self.resources = tuple(resources)
        self.cookResources()

    security.declareProtected(permissions.ManagePortal, 'getResourcePosition')
    def getResourcePosition(self, id):
        """Get the position (order) of an resource given its id."""
        resource_ids = list(self.getResourceIds())
        if id in resource_ids:
            return resource_ids.index(id)
        return -1

    security.declareProtected(permissions.ManagePortal, 'getDevelMode')
    def getDevelMode(self):
        """Are we running in development mode?"""
        import Globals
        return bool(Globals.DevelopmentMode)

    security.declareProtected(permissions.ManagePortal, 'getDebugMode')
    def getDebugMode(self):
        """Is resource merging disabled?"""
        devel = DEVEL_MODE.get(self.id, None)
        if devel is None:
            devel = DEVEL_MODE[self.id] = self.getDevelMode()
        return devel

    security.declareProtected(permissions.ManagePortal, 'setDebugMode')
    def setDebugMode(self, value):
        """Set whether resource merging should be disabled."""
        DEVEL_MODE[self.id] = bool(value)

    security.declareProtected(permissions.View, 'getEvaluatedResources')
    def getEvaluatedResources(self, context, theme=None):
        """Return the filtered evaluated resources."""
        results = self.getCookedResources(theme=theme)
        return [item for item in results if self.evaluate(item, context)]

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
        return output

    security.declareProtected(permissions.View, 'getContentType')
    def getContentType(self):
        """Return the registry content type.

        Should be overwritten by subclasses.
        """
        return 'text/plain'

    security.declarePublic('getCurrentSkinName')
    def getCurrentSkinName(self):
        """Get the currently active skin name
        """

        # For reasons of horridness, we can't use acquisition here
        portal_url = getToolByName(getSite(), 'portal_url')
        return portal_url.getPortalObject().getCurrentSkinName()


InitializeClass(BaseRegistryTool)
