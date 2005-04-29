from Products.CMFCore.utils import ToolInit

from Products.CMFCore.DirectoryView import registerDirectory
from Products.ResourceRegistries.config import PROJECTNAME, SKINS_DIR, GLOBALS
from Products.ResourceRegistries import tools

registerDirectory(SKINS_DIR, GLOBALS)

def initialize(context):

    TOOLS = (
        tools.CSSRegistry.CSSRegistryTool,
        tools.JSRegistry.JSRegistryTool,

    )

    ToolInit(
        PROJECTNAME + ' Tool',
        tools = TOOLS,
        product_name = PROJECTNAME,
        icon = 'tool.gif',
    ).initialize(context)
