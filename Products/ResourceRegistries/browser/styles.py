from Acquisition import aq_inner
from Products.PythonScripts.standard import url_quote
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName


class StylesView(BrowserView):
    """ Information for style rendering. """

    def registry(self):
        return getToolByName(aq_inner(self.context), 'portal_css')

    def skinname(self):
        return aq_inner(self.context).getCurrentSkinName()

    def styles(self):
        registry = self.registry()
        registry_url = registry.absolute_url()
        context = aq_inner(self.context)

        styles = registry.getEvaluatedResources(context)
        skinname = url_quote(self.skinname())
        result = []
        for style in styles:
            rendering = style.getRendering()
            if style.isExternalResource():
                src = "%s" % style.getId()
            else:
                src = "%s/%s/%s" % (registry_url, skinname, style.getId())
            if rendering == 'link':
                data = {'rendering': rendering,
                        'media': style.getMedia(),
                        'rel': style.getRel(),
                        'title': style.getTitle(),
                        'conditionalcomment' : style.getConditionalcomment(),
                        'src': src}
            elif rendering == 'import':
                data = {'rendering': rendering,
                        'media': style.getMedia(),
                        'conditionalcomment' : style.getConditionalcomment(),
                        'src': src}
            elif rendering == 'inline':
                content = registry.getInlineResource(style.getId(), context)
                data = {'rendering': rendering,
                        'media': style.getMedia(),
                        'conditionalcomment' : style.getConditionalcomment(),
                        'content': content}
            else:
                raise ValueError("Unkown rendering method '%s' for style '%s'" % (rendering, style.getId()))
            result.append(data)
        return result
