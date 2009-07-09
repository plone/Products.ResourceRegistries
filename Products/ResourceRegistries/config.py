PROJECTNAME = 'ResourceRegistries'

CSSTOOLNAME = 'portal_css'
CSSTOOLTYPE = 'Stylesheets Registry'

KSSTOOLNAME = 'portal_kss'
KSSTOOLTYPE = 'KSS Registry'

JSTOOLNAME = 'portal_javascripts'
JSTOOLTYPE = 'JavaScripts Registry'

GLOBALS = globals()

CSS_RENDER_METHODS = ('import', 'link', 'inline')
CSS_COMPRESSION_METHODS = ('none', 'safe', 'full')
CSS_EXTERNAL_RENDER_METHODS = ('import','link')
CSS_EXTERNAL_COMPRESSION_METHODS = ('none',)

KSS_COMPRESSION_METHODS = ('none', 'safe', 'full')
KSS_EXTERNAL_COMPRESSION_METHODS = ('none',)

JS_COMPRESSION_METHODS = ('none', 'safe', 'full', 'safe-encode', 'full-encode')
JS_EXTERNAL_COMPRESSION_METHODS = ('none',)

CSS_CACHE_DURATION = 7  # css cache life in days (note: value can be a float)
KSS_CACHE_DURATION = 7  # kss cache life in days (note: value can be a float)
JS_CACHE_DURATION = 7   # js cache life in days (note: value can be a float)
