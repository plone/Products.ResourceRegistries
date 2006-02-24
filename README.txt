ResourceRegistries

  A registry for linked Stylesheet files and Javascripts.

  This registry is mainly aimed at solving the following usecases:

  - Enable product authors to register stylesheets with their product
    installers without having to resort to override either header.pt or
    ploneCustom.css creating potential conflicts with other products.

  - Enable more componentialization of the stylesheets provided with Plone
    (and other products) without having to increase the number of http
    requests for a Plone page.

  - Enable condition checking on stylesheets. Great for variable
    look-and-feel for groups/roles/folders/departments/content-types/etc

  - Enable inline dynamic stylesheets. For those style rules that should
    vary for each request. Mainly used for things like header-bar-
    backgroundimages, department colors etc.

  - Enable developers to activate/deactivate their styles in a simpler way

  - Enable compression to safe bandwidth and download time

Usage

  ResourceRegistries 1.2 requires CMF 1.5.5 or later.

  The CSSRegistry and JSRegistry is configured through the ZMI. it can be found
  in the ZMI of your plonesite as 'portal_css' and 'portal_javascript'.

  Add links to stylesheets that exist in your skins paths, by ids;  like
  'plone.css', 'ploneCustom.css' etc.

  Linked stylesheets take some parameters:

  id -- The id mentioned above. the Zope id of the stylesheet to be used.

  expression -- A CMF expression to be evaluated to check if the stylesheet
  should be included in output or not.

  media -- The media for which the stylesheet should apply, normally empty or
  'all'. other possible values are 'screen', 'print' etc.

  rel -- Link relation. defaults to 'stylesheet', and should almost always
  stay that way. For designating alternative stylesheets.

  rendering -- How to link the stylesheet from the html page:

      - 'import' - the default. normal css import

      - 'link' - works better for old browsers an alternate stylesheets

      - 'inline' - render the stylesheet inline instead of linking it
        externally. Use
        sparingly. Costs bandwidth, but is very useful for style that vary for
        example on a per-folder-basis, like those famous header graphics bars.

  compression -- Whether and how much the resource should be compressed:

      - 'none' - the original content will not be changed

      - 'safe' - the content will be compressed in a way which should be safe
                 for any workarounds for browser bugs

      - 'full' - the content will be heavily compressed, this might break some
                 workarounds, only use this if you know what you are doing

  If several stylesheets listed directly after each other in the registry have
  the same parameters and expression, they will be concatenated into a larger,
  composite, stylesheet on rendering. - This can be useful for splitting
  stylesheets into smaller components for overrideing, while preserving
  cacheability and minimising the number of http-requests to Plone.

  This tool was started at the excellent SnowSprint 2005 - Organised by
  Telesis in the Austrian Alps. Thanks, Jodok! :)

Credits

    Florian Schulze -- Independent
    
    Laurence Rowe -- Independent

    Geir Bækholt -- "Plone Solutions":http://www.plonesolutions.com

    Matt Hamilton -- "Netsight Internet Solutions":http://www.netsight.co.uk

Plone Solutions AS

  "http://www.plonesolutions.com":http://www.plonesolutions.com

  "info@plonesolutions.com":mailto:info@plonesolutions.com

Netsight Internet Solutions

  "http://www.netsight.co.uk":http://www.netsight.co.uk/

  "info@netsight.co.uk":mailto:info@netsight.co.uk
