from xml.dom.minidom import parseString

from Products.CMFCore.utils import getToolByName

from Products.GenericSetup.interfaces import INodeExporter
from Products.GenericSetup.interfaces import INodeImporter
from Products.GenericSetup.interfaces import PURGE, UPDATE
from Products.GenericSetup.utils import PrettyDocument
from Products.GenericSetup.utils import I18NURI
from Products.GenericSetup.utils import NodeAdapterBase


def importResRegistry(context, reg_id, reg_title, filename):
    """
    Import resource registry.
    """
    site = context.getSite()
    mode = context.shouldPurge() and PURGE or UPDATE
    res_reg = getToolByName(site, reg_id)

    body = context.readDataFile(filename)
    if body is None:
        return "%s: Nothing to import" % reg_title

    importer = INodeImporter(res_reg, None)
    if importer is None:
        return "%s: Import adapter missing." % reg_title

    importer.importNode(parseString(body).documentElement, mode=mode)
    return "%s imported." % reg_title

def exportResRegistry(context, reg_id, reg_title, filename):
    """
    Export resource registry.
    """
    site = context.getSite()
    res_reg = getToolByName(site, reg_id, None)
    if res_reg is None:
        return "%s: Nothing to export." % reg_title

    exporter = INodeExporter(res_reg)
    if exporter is None:
        return "%s: Export adapter missing." % reg_title

    doc = PrettyDocument()
    doc.appendChild(exporter.exportNode(doc))
    context.writeDataFile(filename, doc.toprettyxml(' '), 'text/xml')
    return "%s exported" % reg_title


class ResourceRegistryNodeAdapter(NodeAdapterBase):

    def exportNode(self, doc):
        """
        Export the object as a DOM node.
        """
        self._doc = doc
        node = self._getObjectNode('object')
        node.setAttribute('xmlns:i18n', I18NURI)
        child = self._extractResourceInfo()
        node.appendChild(child)
        return node

    def importNode(self, node, mode=PURGE):
        """
        Import the object from the DOM node.
        """
        if mode == PURGE:
            # XXX purge the registry
            pass

        self._initResources(node, mode)

    def _extractResourceInfo(self):
        """
        Extract the information for each of the registered resources.
        """
        fragment = self._doc.createDocumentFragment()
        registry = getToolByName(self.context, self.registry_id)
        resources = registry.getResources()
        for resource in resources:
            data = resource._data.copy()
            child = self._doc.createElement(self.resource_type)
            for key, value in data.items():
                if type(value) == type(True) or type(value) == type(0):
                    value = str(value)
                child.setAttribute(key, value)
            fragment.appendChild(child)
        return fragment

    def _initResources(self, node, mode):
        """
        Initialize the registered resources based on the contents of
        the provided DOM node.
        """
        registry = getToolByName(self.context, self.registry_id)
        reg_method = getattr(registry, self.register_method)
        for child in node.childNodes:
            if child.nodeName != self.resource_type:
                continue

            data = {}
            for key, value in child.attributes.items():
                key = str(key)
                if key == 'id':
                    res_id = str(value)
                elif value.lower() == 'false':
                    data[key] = False
                elif value.lower() == 'true':
                    data[key] = True
                else:
                    try:
                        data[key] = int(value)
                    except ValueError:
                        data[key] = str(value)

            reg_method(res_id, **data)
