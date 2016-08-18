Changelog
=========

3.0.4 (2016-08-18)
------------------

Fixes:

- ``_setId`` was incorrectly rising ``ValueError`` making it impossible to rename an external resource.
  [hvelarde]

- Use zope.interface decorator.
  [gforcada]


3.0.3 (2015-09-22)
------------------

- bugfix: Handle theme names containing a `.` properly in ``manage_bundlesForm``
  [fRiSi]


3.0.2 (2015-05-04)
------------------

- Comment out views from old resource registry so it does not render
  them on Plone 5.  Meanwhile we don't remove the product.  It is
  planned to be removed on Plone 5.1.
  [bloodbare]


3.0.1 (2014-10-23)
------------------

- Use ``application/javascript`` instead of ``application/x-javascript`` for
  the ``Content-Type`` http header of JavaScript resources. Also see:
  http://stackoverflow.com/questions/9664282
  [thet]

- bugfix: do not convert URIs such as
  url(data:image/svg+xml;base64,PD94bWwgdmVyc2lv) to absolute urls
  see https://github.com/plone/Products.ResourceRegistries/pull/16
  [cillianderoiste]

- Include ``insert-after`` as an attribute when exporting ResourceRegistries.
  [saily]


3.0 (2014-04-05)
----------------

- add csrf token to delete urls for resources
  [vangheem]

- Properly handle redirections from login view; resources used to be erased
  on authentication redirect for POST action
  [mihneasim]

- Replace troublesome HTTP_REFERER redirects, they can lead to infinite
  redirects on expired session re-login
  [mihneasim]

- Don't try to traverse to remote objects starting with '//', triggered
  from plone.css
  [eleddy]


2.2.9 (2013-06-13)
------------------

- Allow users to add resources starting with '//', the proper way to link
  to external resources when serving over http and https. This makes it
  much easier to manage content on CDNs.
  [eleddy]


2.2.8 (2013-05-23)
------------------

- Avoid recursive call of _migrateCookedResouces method in BaseTool which
  prevented the old concatenated resource storage from beeing migrated.
  The problem emerged when migrating from Plone 4.2 to 4.3.
  [thet]


2.2.7 (2013-03-05)
------------------

- Fixed some spurious test failures for Expires being off by
  minus one second.
  [maurits]


2.2.6 (2013-01-17)
------------------

- Raise width of resource-id input fields in ZMI from 30 to 80, so that browser
  resource ids can be shown as whole.
  [thet]

- Fixed spurious test failures for Expires being off by one second.
  [maurits]


2.2.5 (2013-01-13)
------------------

- Detect when CSS configuration will cause them to be marked as alternate
  by browsers and warn the user.
  [MatthewWilkes]


2.2.4 (2012-12-09)
------------------

- Add some space between up/down and remove links in ZMI
  [maartenking]

2.2.3 (2012-10-16)
------------------

- Don't break if the site doesn't have a portal_kss registry.
  [davisagli]


2.2.2 (2012-08-29)
------------------

- Changed deprecated getSiteEncoding to hardcoded `utf-8`
  [tom_gross]

2.2.1 (2012-08-11)
------------------

- Make it possible to change the default bundles for a theme by
  assigning bundles to '(default)'
  [davisagli]

2.2 (2012-07-02)
----------------

- Change BaseRegistryTool.deferredGetContent method to use
  OFS.File.update_data instead of OFS.File.manage_upload. The
  manage_upload method is a "ZMI" API.  By calling manage_upload
  an ObjectModifiedEvent would be generated for every resource
  served from the registry.  Let's do less work.
  [runyaga]

2.1.2 (2012-05-25)
------------------

- Fix test failure under Plone 4.2.
  [hannosch]

- using hashlib.md5 (fixing a deprecation warning)
  [ajung]


2.1.1 (2012-05-07)
------------------

- Added theme-parameter for getResourceContent for JavaScriptRegistry.
  Even if it is unused it now allows the same arguments as the
  BaseRegistry
  [tom_gross]

- Added support for OFS.Image.File-objects using OFS.Image.PData
  This fixes https://dev.plone.org/ticket/12479
  [datakurre]

2.1 (2012-04-18)
----------------

- Use iterative magic number generation based on the properties of all
  included resources (for each concatenated resource).

  This fixes an issue with external caches where resources for
  different content would sometimes get assigned the same resource id
  (due to the previous implementation using a random integer), making
  it impossible to cache a resource correctly without additional
  information.
  [malthe]


2.1a1 (2011-06-28)
------------------

- Add bundle concept - a bundle is a string tag against a resource, which can
  be used to filter resources by theme. Each theme has a list of enabled
  bundles, managed on the 'Bundles' tab in the ZMI (note that this is global).
  [optilude]

- Fix handling of the purge attribute on import.
  [rossp]


2.0.8 (2012-03-14)
------------------

- Add time element. This is necessary for the generated ids to update
  on any save, to reflect possible updates in the served content.
  [malthe]


2.0.7 (2012-03-14)
------------------

- Fixed ZMI screens to render for resources containing query strings in their
  ids, like found in the plone.session refresh support.
  [hannosch]


2.0.6 (2011-11-24)
------------------

- Fixed "AttributeError: 'FileResourceXX' object has no attribute 'POST'
  when displaying inline resources when using a POST request.
  Fixes http://dev.plone.org/ticket/8998
  [maurits]


2.0.5 - 2011-07-19
------------------

- Switched <link rel="kinetic-stylesheet" type="text/css" /> to <link
  rel="stylesheet" data-rel="kinetic-stylesheet" type="text/kss" /> to fix HTML5
  validation. References http://dev.plone.org/plone/ticket/11300
  [spliter]

- Add MANIFEST.in.
  [WouterVH]


2.0.4 - 2011-04-15
------------------

- Bugfix for #9849. Incomplete caching.
  [do3cc]


2.0.3 - 2011-03-02
------------------

- Support merging of resources that return IStreamIterators
  [optilude]


2.0.2 - 2010-07-18
------------------

- Update license to GPL version 2 only.
  [hannosch]


2.0.1 - 2010-07-15
------------------

- Silence the `Nothing to import.` log messages.
  [hannosch]


2.0 - 2010-07-01
----------------

- Changed the registries moveResourceAfter and moveResourceBefore methods to
  gracefully handle missing destination ids. This is useful for GenericSetup
  upgrade steps to work even if the resources specified in "insert-after" or
  "insert-before" do not exist.
  [hannosch]


2.0b5 - 2010-06-13
------------------

- Avoid deprecation warnings under Zope 2.13.
  [hannosch]

- Adjusted tests to match new content-type for JavaScript in Zope 2.12.7+.
  [hannosch]


2.0b4 - 2010-06-03
------------------

- Add purge support to export/import handlers.
  [elro]

- Fix the authenticated checkbox on the kss form.
  [elro]


2.0b3 - 2010-05-01
------------------

- Add an option 'applyPrefix' to stylesheets. This can be set in the UI, in
  the various constructor methods, or as an attribute in a cssregistry.xml
  file. It defaults to false. It has no effect in debug mode. In non-debug-
  mode, however, it will parse a stylesheet for 'url()' statements that
  contain *relative* paths. These will be prefixed with the Plone site path.
  If the stylesheet id contains a path (e.g. '++resource++foo/css/bar.css')
  this will be used in the prefix as well. The goal is to make relative paths
  internal to a resource directory work, even when resource merging is used.
  Previously, it'd break because resource merging changes the URL.
  [optilude]


2.0b2 - 2010-01-24
------------------

- Apply a marker interface ICookedFile to the files created on the fly for
  cooked/concatenated resources returned by ResourceRegistries. This makes
  it easier to detect these for caching purposes and treat them differently
  to in-ZODB files, which may also be instances of OFS.Image.File.
  [optilude]


2.0b1 - 2009-12-27
------------------

- Marked zope.component as a real dependency of this package.
  [hannosch]


2.0a2 - 2009-12-20
------------------

- Cleaned up some old charset related fallback code.
  [hannosch]

- Changed the development mode to be a non-persistent setting. By default it
  follows the Zope development mode (bin/instance fg vs. bin/instance console).
  The setting can be changed during process runtime.
  [hannosch]


2.0a1 - 2009-11-16
------------------

- Declare 'screen' to be the default for the media attribute instead of None.
  It is the most commonly used one in Plone's own themes.
  [hannosch]

- Fixed typo in update process of authenticated resources. Fixes #9599
  [naro]

- Fixed JS packer to be a little less greedy about protecting regular
  expressions. This fixes #8790.
  [dunlapm]

- Changed the order of CSS/JS rendering, CSS now renders first to allow the
  browser to get it as soon as possible, to avoid the "flash of unstyled
  content"
  [limi]

- Removed some whitespace in the rendering templates for JS, CSS and KSS to make
  the source rendering more readable. These are very small and understandable
  templates, so we'd rather have some noise there than on the front end.
  [limi]

- Removed the `autogroupingmode` feature. In practice it turned out to work
  not so well and caused hard to debug problems.
  [hannosch]

- Automatically set the registries into development mode if Zope itself runs
  in development mode.
  [hannosch]

- Get the tests working again under Plone 5 and make sure we handle
  zope.app.publisher file resources correctly under repoze.zope2.
  [hannosch]

- Added missing InitializeClass call for BaseRegistryTool.
  [davisagli]

- Changed default values for resources to more sensible values.
  [hannosch]

- Restructured documentation files.
  [hannosch]

- Added `authenticated` as a new option to all resources. If a resource is
  marked this way, it will only be shown for authenticated users. This makes
  the most common use-case of restricting resources to logged-in users easier
  and allows to optimize the internal API for speed for this use-case. An
  expression on a resource is ignored if the authenticated flag is set.
  [hannosch]

- Removed BBB imports and code. We require Zope 2.12 now.
  [hannosch]

- Handle a missing portal_kss tool gracefully in the kineticstylesheets
  viewlet.
  [hannosch]

- Added BBB imports to make sure the InitializeClass can be imported in
  Zope versions before 2.12.
  [hannosch]

- Avoid dependency on the zope.app.zapi package.
  [hannosch]

- Declare package dependencies, fixed deprecation warnings for use of
  Globals and changed error raising to be forward compatible.
  [hannosch]

- Change the fix for #7522 made in 1.4.3. For inline resources we pass
  Unicode down into the page templates. The TAL machinery expects to get
  Unicode and not encoded strings.
  [hannosch]


1.5.3 - 2009-05-17
------------------

- Allow setting of debug mode in registries through Generic Setup
  profiles. This closes http://dev.plone.org/plone/ticket/8712
  [dunlapm]

- Fixed error with inline z3resources not being able to handle a POST
  request. This fixes http://dev.plone.org/plone/ticket/8998
  [dunlapm]


1.5.2 - 2009-04-21
------------------

- Fixed error with the conditional comment being lost when adding a new
  Resource when adding a new entry to the JS or CSS registries.
  [dunlapm]

- Fixed error with GS Export/Import. Fixes
  http://dev.plone.org/plone/ticket/9154
  [dunlapm]


1.5.1 - 2009-04-14
------------------

- Put CDATA start and end markers in a javascript comment. Fixes
  http://dev.plone.org/plone/ticket/9128
  [wichert]


1.5.0 - 2009-03-01
------------------

- Removed the uppermost Save button from the ZMI pages for registries.
  Clicking this button before the registry page has finished loading could
  lead to data loss.
  [dunlapm, fschulze]

- Resources beginning with "http://" or "https://" are now valid and may be
  included as resources. Registries will automatically disable merging,
  caching, compression, and inline rendering of external resources. This
  closes http://dev.plone.org/plone/ticket/8312
  [dunlapm, fschulze]

- Added option to have a conditional comment attached to a given resource.
  Currently the UI only supports this behavior with the CSS and JavaScript
  Registries, but the underpinnings for the KSS registry is in place.
  This closes http://dev.plone.org/plone/ticket/5521
  [dunlapm, fschulze]

- Do not try to export the `cooked_expression` into the GenericSetup
  profiles. It is only an internal optimization and the value is reflected
  in the `expression` value.
  [hannosch]

- Store the cooked expressions as a real persistent expression object,
  instead of compiling the expression on every view.
  [hannosch]

- Added 'context' as an alias for 'object' in action expressions.
  [davisagli, hannosch]


1.4.3 - 2008-10-08
------------------

- Eggified into Products.ResourceRegistries.

- Fixed error where non-traversable resources could be registered. This closes
  http://dev.plone.org/plone/ticket/8153
  [dunlapm]

- Ensure that resources can be removed in xml.
  [maurits]

- Purge old zope2 Interface interfaces for Zope 2.12 compatibility.
  [elro]

- Encode inline resources using the site encoding.
  Fixes http://dev.plone.org/plone/ticket/7522
  [wichert]

- Fixed potential Acquisition problems in viewlets.
  [hannosch]


1.4.2 - 2008-03-06
------------------

- Properly encode the resource id. This fixes moving of resource without JS
  and removing recources which contain special chars like plus signs.
  Fixes http://dev.plone.org/plone/ticket/7482
  [fschulze]

- Revert part of r7143: returning NotFound from a API call is never
  the right thing to do since it makes the publisher show a object-not-found
  page, hiding the real error. Restore the old behaviour and raise a
  ValueError instead. This fixes mysterious not-found errors from
  GenericSetup imports.
  [wichert]

- Support Z3 template resources (not just file and image resources).
  [mj]


1.4.1 - 2007-10-10
------------------

- Added '/' to the strings that are filtered out in
  BaseRegistry.generateId(). This fixes #7048.
  [davconvent]


1.4.0 - 2007-08-16
------------------

- Add support for automatic grouping mode to the GenericSetup export/import
  code.
  [wichert]


1.4.0-rc1 - 2007-07-09
----------------------

- Added a new automatic grouping mode feature. It is turned off by default.
  When enabled the resources will first be sorted into groups with the same
  merging-relevant settings and after that merged. In the groups the order of
  the resources in the registries will be preserved.
  [hannosch]

- Changed the exportimport handlers to only cook the resources once at the end
  and not after each new resource has been added.
  [hannosch]


1.4.0-beta5 - 2007-05-02
------------------------

- Fixed setting of cache headers when the registry is associated with a
  RAMCache.
  [fschulze]


1.4.0-beta4 - 2007-04-30
------------------------

- Switched back to getToolByName.
  [wichert]

- Added portal_kss as registry for kss files.
  [fschulze]

- Slightly optimized the viewlet manager templates.
  [hannosch]


1.4.0-beta3 - 2007-03-25
------------------------

- Replace usage of getToolByNames with getUtility.
  [wichert, hannosch]


1.4.0-beta2 - 2007-03-01
------------------------

- Reverted fix of tests, because Zope was wrong.
  [fschulze]


1.4.0-beta1 - 2007-02-27
------------------------

- Fixed test failures caused by changes in Zope 2.10.
  [fschulze]

- Ported bugfixes from 1.3 line.
  [fschulze]


1.4.0-alpha2 - 2007-02-11
-------------------------

- Started to use views and viewlet managers.
  [fschulze]

- Removed compatibility stuff for Plone version lower than 3.0.
  [fschulze]


1.3.8 - 2007-04-16
------------------

- Cook resources after GS profile import.
  [fschulze]

- Added missing enabled property handling to updateScript.
  [fschulze]

- Fixed typo which prevented position-after/insert-after in GS profiles to
  work.
  [fschulze]


1.3.7 - 2007-03-25
------------------

- For compatibility with GenericSetup conventions, the import steps now
  support 'insert-before' and  'insert-after' as aliases for
  'position-before' and 'position-after', while 'insert-top' and
  'insert-bottom' are aliases for 'position-top' and 'position-bottom',
  respectively.
  [mj]


1.3.6 - 2007-02-27
------------------

- Invalidate cache when cooking resources if the registry is assigned to a
  RAMCache or similar cache manager.

- Fixed string replacement during packing when several resources got packed
  in different threads at once, which resulted in exchanged strings.
  [fschulze]


1.3.5 - 2007-02-11
------------------

- Fixed string protection for strings which mix single and double quotes.
  [fschulze]

- Made packer.py usable as a standalone commandline tool.
  [fschulze]

- Fixed several issues in 'full' compression.
  [fschulze]

- Extended the GenericSetup import step to support positioning of resources:
  the 'position-before' and 'position-after' attributes cause the resource
  to be positioned before or after resource named in the attribute.
  'position-top' and 'position-bottom' move a resource to the top or bottom.
  [mj]


1.3.4 - 2007-01-03
------------------

- Improved IE conditional compilation protection, it now works in "full"
  compression.
  [fschulze]

- Improved regular expression for strings.
  [fschulze]

- Fixed order of oneline and multiline comment removal in javascript packer.
  [fschulze]

- Fixed validation warning about multiple comments when rendering resources
  inline.
  [fschulze]

- Made css "full" packing more aggressive.
  [fschulze]

- Cleaned up testing framework and made all tests run properly.
  [fschulze, hannosch]


1.3.3 - 2006-12-13
------------------

- Don't wrap None in aquisition wrapper if resource is not found.
  [tesdal]


1.3.2 - 2006-09-11
------------------

- Made GenericSetup importer not fail on repeated imports.
  [alecm]

- Made enabled checkbox work again.
  [fschulze]


1.3.1 - 2006-08-17
------------------

- Enable use of z3 / Five resources.
  [ree]

- Mark missing or unaccessible ressources in management screens.
  [fschulze]

- Moved 'enabled' checkbox into legend before 'id' textbox.
  [fschulze]

- Don't remove conditional compile instructions for IE from javascripts.
  [fschulze]

- Fixed error when content is unicode.
  [rocky]


1.3 - 2006-07-16
----------------

- No changes since rc1.


1.3-rc1 - 2006-06-02
--------------------

- Add patch from jenner to handle updating and removal of resources
  from GenericSetup profiles.
  [wichert]


1.3-beta2 - 2006-05-17
----------------------

- Included fixes from the 1.2 line.
  [fschulze]


1.3-beta1 - 2006-03-31
----------------------

- Do not install default CSS and JS on upgrade, only on initial installation.
  [wichert]


1.3-alpha1 - 2006-02-24
-----------------------

- Added GenericSetup import/export handlers (to support GS-based Plone 2.5
  portal creation)
  [rafrombrc]


1.2.4 - 2006-09-11
------------------

- Made enabled checkbox work again.
  [fschulze]


1.2.3 - 2006-09-06
------------------

- Backported several fixes from 1.3.1:
  [fschulze]

- Enable use of z3 / Five resources.
  [ree]

- Mark missing or unaccessible ressources in management screens.
  [fschulze]

- Moved 'enabled' checkbox into legend before 'id' textbox.
  [fschulze]

- Don't remove conditional compile instructions for IE from javascripts.
  [fschulze]

- Fixed error when content is unicode.
  [rocky]


1.2.2 - 2006-05-15
------------------

- Added missing arguments in resource adding functions.
  [jenner, fschulze]


1.2.1 - 2006-04-13
------------------

- Fixed traversal of security restricted resources.
  [jenner, alecm, fschulze]

- Added javascript "full" compression, which achieves higher compression ratios
  by doing variable name packing based on the rules from Dean Edwards packer:
  http://dean.edwards.name/packer/usage/
  [fschulze]

- Added keyword encoding for javascript. This greatly reduces the file size of
  javascript files, but adds a small performance hit on the client for the
  decoding.
  [fschulze]


1.2 - 2006-02-24
----------------

- Added compression for CSS and Javascript resources.
  [fschulze]

- Added better labels and a short explanation to the debugmode-checkbox in the forms.
  [elvix]

- Renamed 'TAL condition' to 'Condition' in the forms, as it has nothing to do with
  TAL at all (it is a CMF/TALES expression) It should include a link to CMF Expressions help
  [elvix]


1.1 - 2006-11-22
----------------

- Fixed cooking of resources to ensure that uncookable resources are not merged.
  [elro]

- Fixed tests for unauthorized to accept a 401 as an unauthorized error.
  [elro]

- Fixed setDebugMode to recook resources after being changed.
  [elro]


1.1b1
-----

- Added checkbox to configure cacheability of resources.
  [fschulze]

- Made registries cacheable. This is most useful with the RAMCacheManager.
  Just associate portal_css and portal_javascripts with the RAMCache.
  [fschulze]

- Apply magic id to all resources when not in debug mode, so invalidation
  works.
  [fschulze]

- Made skin aware. This now depends on getCurrentSkinName added in CMF 1.5.5.
  [elro]


1.0.5 - 2005-09-09
------------------

- Fixed encoding of javascripts.
  [fschulze]


1.0.4 - 2005-09-03
------------------

- Fixed reordering of resources with javascript.
  [fschulze]


1.0.3 - 2005-08-17
------------------

- Fixed typo in the migration external method which lead to portal_javascripts
  not being migrated.
  [fschulze]

- Small fixes to UI.
  [limi]


1.0.2 - 2005-08-09
------------------

- Fix for bug #4392, where merging FSfiles could mess up http-status headers
  and cause weird hanging in browsers.
  [plonista, fschulze, elvix]


1.0.1
-----

- Don't filter resources in merged overview in ZMI.
  [fschulze]

- Improved management UI.
  [limi, fschulze]

- Fixed reinstall bug due to improper resource id lookup.
  [alecm]


1.0 - 2005-08-01
----------------

- Moved directory with skin layer for Plone 2.0.5 compatibility to product
  root, so it doesn't interfere with Plone 2.1. The version check on install
  time didn't seem to be enough.
  [fschulze]

- getTitle and getMedia will return None now if they are empty, this removes
  empty title and media attributes from the generated HTML.

- Fixed reordering of resources in ZMI when javascript is enabled.
  [fschulze, jenner]

- Fixed submitting changes in ZMI for stylesheets on IE.
  [fschulze]


0.95 - 2005-07-03
-----------------

- Added getResource function. This allows to change properties of each
  resource. After that, a call to cookResources is needed.
  [fschulze]

- Added getResourceIds function.
  [fschulze]

- Added test for context dependancy to inline css rendering.
  [dom]

- Now uses restrictedTraverse() rather than getattr() for returning resources,
  to provide support for resources held within the ZODB.
  [dom]

- Added a "is merging allowed?" option ("cookable" property) to determine where
  a resource can be merged (default True). This was added because objects in
  the ZODB may have variable permissions but be merged together. Whilst the
  objects are checked at each REQUEST, a new REQUEST won't actually be made
  each time because of the cache headers set on merged resources. If this
  worries you, the simplest solution is not to merge such resources, hence this
  option.
  [dom]

- Added renameResource function with tests.
  [fschulze]

- In Plone 2.1 plone_javascripts.js was removed, fixed tests by using
  jstest.js from our own skin.
  [dom]


0.9
---

- Fixed function of enabled checkbox when adding css/javascript from ZMI.
  Added title field to the 'add stylesheet' part in the ZMI.
  [fschulze]

- Added migration script for old instances. Just create a external method with
  id 'migrate_resourceregistries', Module Name 'ResourceRegistries.migrate' and
  Function Name 'migrate' and click on the 'Test' tab.
  [fschulze]

- Cleaned up imports and whitespaces. Code standardization and small
  improvements. Fixed ZMI templates XHTML markup.
  [deo]

- Refactored the two registries to use one common base class.
  [fschulze]

- Refactored moving functions, so we have more possibilities. The API reflects
  the IOrderedContainer one.
  [fschulze]

- Fix order of javascripts, the topmost in the management screen also needs
  to be the topmost in the resulting source.
  [fschulze]

- Added debugmode where scripts are not concatenated. This will let things
  like the javascript console point to the right line-number. And makes it
  easier to develop, because there is no caching of the scripts.
  [fschulze]

- Fixed cooking of stylesheets so that composite stylesheets get correct
  media settings. Thanks a lot to Denis Mishunoff[spliter] for discovery,
  investigation and suggested fix
  [elvix]

- Fixed some security declarations.
  [fschulze]

- Made moving of stylesheets and javascripts in ZMI possible without javascript
  being enabled in the browser.
  [fschulze]

- Moved 2.0.5 header.pt to skins/ResourceRegistries_20compatibility and
  remove ResourceRegistries_20compatibility when Plone != 2.0.x
  [fschulze]

- Check existance of stylesheets and javascripts before registering. This
  fixes reinstallation.
  [fschulze]

- Removed duplicate getScripts function definition in tools/JSRegistry.py
  [fschulze]

- Fixed JSRegistry for Plone < 2.1 where plone_utils.getSiteEncoding is not
  available.
  [fschulze]

- Renamed config.TOOLNAME to config.CSSTOOLNAME
  and config.TOOLTYPE to config.CSSTOOLTYPE
  [batlogg]

- Added tests for attributes on stylesheets. About time.
  [elvix]

- Added title for alternate stylesheets.
  [fschulze]

- Removing superflous skins directories.
  [elvix]

- Added new debugmode where stylesheets are not concatenated. This will let
  things like the DOM inspector in Mozilla point to the right line-number.
  [ldr] [elvix]

- Added bugfix for handling disabled items when cooking stylesheets.
  [fschulze]


0.8 - 2005-05-21
----------------

- Renamed to ResourceRegistries instead of the historical and wrong
  CSSRegistry.
  [elvix]

- Upgraded JSRegistry to have a more proper ZMI form, now with reordering
  support.
  [elvix]

- Changed the order elements are added to the JSRegistry.
  [elvix]

- Added license/copyright notice to composite files (neccesary for including
  for third party stuff).
  [elvix]

- Bugfix fixing ZMI form for CSSRegistry.
  [fschulze]


0.7
---

- Added to Plone 2.1 migrations, added installation of the default
  Plone javascripts and stylesheets.
  [elvix]

- Make sure we intercept all requests for objects, even those already
  present in the acquisition chain. Override __bobo_traverse__.
  [elvix]

- Handle cache settings in http headers for served files.
  [elvix]

- Handle http headers for inline scripts and stylesheets.
  [elvix]

- Use explicit </script> tag since these pages are being served as
  text/html. Both IE and firefox will have problems otherwise.
  [bmh]


0.6 and earlier
---------------

- Added a simple readme with basic documentation.
  [elvix]

- Started HISTORY.txt (somewhat late perhaps, but better than never).
  [elvix]

- Cleaned up forms. Better alignment.
  [elvix]

- Separate JSRegistry and CSSRegistry to two tools.
  [elvix]

- Lots of changes, numerous fixes.
  [elvix]


Snowsprint 2005
---------------

- Designed and built first version of the CSSregistry.
  [HammerToe, elvix]
