from Interface import Interface 

class ICSSRegistry(Interface):
    """A tool for registering and evaluating stylesheet and script linkage"""
    
    def registerStylesheet(id, expression='', media='', rel='stylesheet', cssimport=0, inline=0, enabled=1 ):
        """ register a stylesheet """
        

    def getEvaluatedStylesheets(context):
        """ 
        get the evaluated Stylesheet links and inline styles 
        appropriate to the context for rendering
        """
        
    def unregisterStylesheet(sheetid):
        """unregister a registered stylesheet"""
                    
    def getStylesheets():
        """ get the stylesheet objects. For use in management screens"""
                
    def manage_saveStylesheets(data):
        """ 
        save stylesheet data from form submission
        data should be a list or tuple of records or dictionaries
        """
        
        
class IJSRegistry(Interface):
    
    def registerScript(id, expression='', contenttype='text/javascript', inline=0, enabled=1):
        """ register a script"""
            
    def unregisterScript(id):
        """ unregister e registered script"""
            
    def getEvaluatedScripts(context):
        """
        get the evaluated Stylesheet links and inline styles 
        appropriate to the context for rendering
        """

    def getScripts():
        """ get the scripts. For use in management screens"""

    def manage_saveScripts(data):
        """"
        save script data from form submission
        data should be a list or tuple of records or dictionaries
        """
