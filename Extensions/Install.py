from StringIO import StringIO
from Products.Archetypes.Extensions.utils import install_subskin
from Products.CSSRegistry.config import *

def install(self):
    out = StringIO()

    install_subskin(self, out, GLOBALS)

    # Install the CSSRegistry
    if TOOLNAME not in self.objectIds():
        factory = self.manage_addProduct['CSSRegistry']
        factory.manage_addTool(TOOLTYPE)
        print >> out, 'Added CSSRegistry'
    else:
        print >> out, 'CSSRegistry already exists.'

    # Install the JSRegistry
    if JSTOOLNAME not in self.objectIds():
        factory = self.manage_addProduct['CSSRegistry']
        factory.manage_addTool(JSTOOLTYPE)
        print >> out, 'Added JSRegistry'
    else:
        print >> out, 'JSRegistry already exists.'

    return out.getvalue()
