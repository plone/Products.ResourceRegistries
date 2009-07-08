from Acquisition import aq_inner
from Products.PythonScripts.standard import url_quote
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName


class ScriptsView(BrowserView):
    """ Information for script rendering. """

    def registry(self):
        return getToolByName(aq_inner(self.context), 'portal_javascripts')

    def skinname(self):
        return aq_inner(self.context).getCurrentSkinName()

    def scripts(self):
        registry = self.registry()
        registry_url = registry.absolute_url()
        context = aq_inner(self.context)

        scripts = registry.getEvaluatedResources(context)
        skinname = url_quote(self.skinname())
        result = []
        for script in scripts:
            inline = bool(script.getInline())
            if inline:
                content = registry.getInlineResource(script.getId(), context)
                data = {'inline': inline,
                        'conditionalcomment' : script.getConditionalcomment(),
                        'content': content}
            else:
                if script.isExternalResource():
                    src = "%s" % (script.getId(),)
                else:
                    src = "%s/%s/%s" % (registry_url, skinname, script.getId())
                data = {'inline': inline,
                        'conditionalcomment' : script.getConditionalcomment(),
                        'src': src}
            result.append(data)
        return result
