import re
import os.path

URL_MATCH = re.compile(r'''(url\s*\(\s*['"]?)(?!data:)([^'")]+)(['"]?\s*\))''', re.I | re.S)

def makeAbsolute(path, prefix):
    """Make a url into an absolute URL by applying the given prefix
    """
    
    # Absolute path or full url
    if path.startswith('/') or '://' in path:
        return path
    
    absolute = "%s/%s" % (prefix, path)
    if '://' in absolute:
        return absolute
    
    normalized = os.path.normpath(absolute)
    if os.path.sep != '/':
        normalized = normalized.replace(os.path.sep, '/')
    return normalized

def applyPrefix(cssSource, prefix):
    """Return a copy of the string cssSource with each url() expression that
    contains an absolute path turned into an absolute path, by applying the
    given prefix.
    """
    
    if prefix.endswith('/'):
        prefix = prefix[:-1]
    
    return URL_MATCH.sub(
            lambda m: m.group(1) + makeAbsolute(m.group(2), prefix) + m.group(3),
            cssSource
        )
