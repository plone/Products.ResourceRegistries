from StringIO import StringIO
from Products.Archetypes.Extensions.utils import install_subskin
from Products.CSSRegistry.config import *

def install(self):
    out = StringIO()

    install_subskin(self, out, GLOBALS)

    if TOOLNAME not in self.objectIds():
        factory = self.manage_addProduct['CSSRegistry']
        factory.manage_addTool(TOOLTYPE)
        factory.manage_addTool(JSTOOLTYPE)

        print >> out, 'Added CSSRegistry Tool.'
    else:
        print >> out, 'CSSRegistry Tool already exists.'

    return out.getvalue()
