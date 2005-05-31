from Interface import Interface

class ICSSRegistry(Interface):
    """A tool for registering and evaluating stylesheet and script linkage"""

    def registerStylesheet(id, expression='', media='', rel='stylesheet', rendering='import', enabled=1 ):
        """ register a stylesheet """

    def getEvaluatedStylesheets(context):
        """
        get the evaluated Stylesheet links and inline styles
        appropriate to the context for rendering
        """

    def unregisterStylesheet(id):
        """unregister a registered stylesheet"""

    def moveStylesheet(id, direction):
        """ move a registered stylesheet in given direction"""

    def getStylesheets():
        """ get the stylesheet objects. For use in management screens"""

    def manage_addStylesheet(id, expression='', media='', rel='stylesheet', rendering='import', enabled=True , REQUEST=None):
        """ Add stylesheet from a ZMI form"""

    def manage_removeStylesheet(id, REQUEST=None):
        """ remove stylesheet from the ZMI"""

    def manage_saveStylesheets(REQUEST=None):
        """
        save stylesheet data from form submission
        """

    def manage_moveStylesheet(id, direction, REQUEST=None):
        """ move stylesheet direction='up'|'down' via the ZMI"""


class IJSRegistry(Interface):

    def registerScript(id, expression='', inline=False, enabled=True):
        """ register a script"""

    def unregisterScript(id):
        """ unregister e registered script"""

    def moveScript(id, direction):
        """ move a registered script in given direction"""

    def getEvaluatedScripts(context):
        """
        get the evaluated Stylesheet links and inline styles
        appropriate to the context for rendering
        """

    def getScripts():
        """ get the scripts. For use in management screens"""

    def manage_saveScripts(REQUEST=None):
        """"
        save script data from form submission
        """

    def manage_addScript(id, expression='', inline=False, enabled=True , REQUEST=None):
        """ Add script from a ZMI form"""

    def manage_removeScript(id, REQUEST=None):
        """ remove script via the ZMI"""

    def manage_moveScript(id, direction, REQUEST=None):
        """ move script direction='up'|'down' via the ZMI"""

