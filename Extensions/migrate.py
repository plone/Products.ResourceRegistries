from Acquisition import aq_base

from Products.ResourceRegistries.config import *
from Products.CMFCore.utils import getToolByName

from StringIO import StringIO

try:
    from CMFPlone.utils import base_hasattr
except ImportError:
    def base_hasattr(obj, name):
        """Like safe_hasattr, but also disables acquisition."""
        return safe_hasattr(aq_base(obj), name)
    
    
    def safe_hasattr(obj, name, _marker=object()):
        """Make sure we don't mask exceptions like hasattr().
    
        We don't want exceptions other than AttributeError to be masked,
        since that too often masks other programming errors.
        Three-argument getattr() doesn't mask those, so we use that to
        implement our own hasattr() replacement.
        """
        return getattr(obj, name, _marker) is not _marker

def migrate(self):
    out = StringIO()
    migrate_cssreg(self, out)
    migrate_jsreg(self, out)
    return out.getvalue()

def migrate_cssreg(self, out):
    print >> out, "Migrating CSSRegistry."
    cssreg = getToolByName(self, 'portal_css', None)
    if cssreg is not None:
        if base_hasattr(cssreg, 'stylesheets'):
            stylesheets = list(cssreg.stylesheets)
            stylesheets.reverse() # the order was reversed
            cssreg.resources = tuple(stylesheets)
            del cssreg.stylesheets
    
        if base_hasattr(cssreg, 'cookedstylesheets'):
            cssreg.cookedresources = cssreg.cookedstylesheets
            del cssreg.cookedstylesheets
    
        if base_hasattr(cssreg, 'concatenatedstylesheets'):
            cssreg.concatenatedresources = cssreg.concatenatedstylesheets
            del cssreg.concatenatedstylesheets
        cssreg.cookResources()
        print >> out, "Done migrating CSSRegistry."
    else:
        print >> out, "No CSSRegistry found."

def migrate_jsreg(self, out):
    print >> out, "Migrating JSRegistry."
    jsreg = getToolByName(self, 'portal_javascripts', None)
    if jsreg is not None:
        if base_hasattr(jsreg, 'scripts'):
            jsreg.resources = jsreg.scripts
            del jsreg.scripts
    
        if base_hasattr(jsreg, 'cookedscripts'):
            jsreg.cookedresources = jsreg.cookedscripts
            del jsreg.cookedscripts
    
        if base_hasattr(jsreg, 'concatenatedscripts'):
            jsreg.concatenatedresources = jsreg.concatenatedscripts
            del jsreg.concatenatedscripts
        jsreg.cookResources()
        print >> out, "Done migrating JSRegistry."
    else:
        print >> out, "No JSRegistry found."
