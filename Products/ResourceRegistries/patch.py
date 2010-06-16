from Acquisition import aq_parent
import Products.Five.browser.resource

_original_DirectoryResource_get = Products.Five.browser.resource.DirectoryResource.get

def DirectoryResource_get(*args, **kwargs):
    # This monkeypatch allows traversal of directoryresource object that
    # also contain a directory that contains the final resource
    # i.e. ++resource++foo/css/bar.css
    resource = _original_DirectoryResource_get(*args, **kwargs)
    if getattr(resource, '__roles__', None) is None:
        resource.__roles__ = aq_parent(resource).__roles__
    return resource
