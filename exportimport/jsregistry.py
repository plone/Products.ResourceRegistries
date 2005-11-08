from xml.dom.minidom import parseString

from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.interfaces import INodeExporter
from Products.GenericSetup.interfaces import INodeImporter
from Products.GenericSetup.interfaces import PURGE, UPDATE
from Products.GenericSetup.utils import PrettyDocument
from Products.GenericSetup.utils import NodeAdapterBase
from Products.GenericSetup.utils import I18NURI

from Products.ResourceRegistries.interfaces import IJSRegistry

_FILENAME = 'jsregistry.xml'

def importJSRegistry(context):
    """
    Import javascript registry.
    """
    site = context.getSite()
    mode = context.shouldPurge() and PURGE or UPDATE
    jsreg = getToolByName(site, 'portal_javascripts')

    body = context.readDataFile(_FILENAME)
    if body is None:
        return "JSRegistry: Nothing to import"

    importer = INodeImporter(jsreg, None)
    if importer is None:
        return "JSRegistry: Import adapter missing."

    importer.importNode(parseString(body).documentElement, mode=mode)
    return "Javascript registry imported."

def exportJSRegistry(context):
    """
    Export javascript registry.
    """
    site = context.getSite()
    jsreg = getToolByName(site, 'portal_javascripts', None)
    if jsreg is None:
        return "JSRegistry: Nothing to export."

    exporter = INodeExporter(jsreg)
    if exporter is None:
        return "JSRegistry: Export adapter missing."

    doc = PrettyDocument()
    doc.appendChild(exporter.exportNode(doc))
    context.writeDataFile(_FILENAME, doc.toprettyxml(' '), 'text/xml')
    return "Javascript registry exported"

class JSRegistryNodeAdapter(NodeAdapterBase):
    """
    Node im- and exporter for JSRegistry.
    """

    __used_for__ = IJSRegistry

    def exportNode(self, doc):
        """
        Export the object as a DOM node.
        """
        self._doc = doc
        node = self._getObjectNode('object')
        node.setAttribute('xmlns:i18n', I18NURI)
        return node
