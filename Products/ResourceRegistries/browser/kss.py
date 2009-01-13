from Acquisition import aq_inner

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.PythonScripts.standard import url_quote


class KSSView(BrowserView):
    """ Information for kss rendering. """

    def registry(self):
        return getToolByName(aq_inner(self.context), 'portal_kss')

    def skinname(self):
        return aq_inner(self.context).getCurrentSkinName()

    def kineticstylesheets(self):
        registry = self.registry()
        registry_url = registry.absolute_url()
        context = aq_inner(self.context)

        kineticstylesheets = registry.getEvaluatedResources(context)
        skinname = url_quote(self.skinname())
        result = []
        for kss in kineticstylesheets:
            if kss.isExternalResource():
                src = "%s" % (kss.getId(),)
            else:
                src = "%s/%s/%s" % (registry_url, skinname, kss.getId())
            data = {'src': src}
            result.append(data)
        return result
