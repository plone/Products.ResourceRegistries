from Interface import Interface 

class ICSSRegistry(Interface):
    """A tool for registering and evaluating stylesheet and script linkage"""
    
    def registerStylesheet(id, expression='', media='', rel='stylesheet', cssimport=0, inline=0, enabled=1 ):
        """ register a stylesheet """
        
    def unregisterStyleheet(id ):
        """unregister a registered stylesheet"""
    
    def registerScript(id, expression='', contenttype='text/javascript', inline=0, enabled=1):
        """ register a script"""
            
    def unregisterScript(id):
        """ unregister e registered script"""
        
    def getEvaluatedStyleheets(context):
        """ 
        get the evaluated Stylesheet links and inline styles 
        appropriate to the context for rendering
        """
        
    def getEvaluatedScripts(context):
        """
        get the evaluated Stylesheet links and inline styles 
        appropriate to the context for rendering
        """
        
    def getStylesheets():
        """ get the styleseet objects. For us in management screens"""
        
    def getScripts():
        """ get the scripts. For us in management screens"""
        
    def manage_saveStylesheet(data):
        """ 
        save stylesheet data from form submission
        data should be a list or tuple of records or dictionaries
        """
        
    def manage_saveScripts(data):
        """"
        save script data from form submission
        data should be a list or tuple of records or dictionaries
        """
        

    
    
