from Products.CMFCore.utils import ToolInit
from Products.CMFCore.DirectoryView import registerDirectory

from Products.ResourceRegistries import tools
from Products.ResourceRegistries import config

registerDirectory(config.SKINS_DIR, config.GLOBALS)

def initialize(context):

    TOOLS = (
        tools.CSSRegistry.CSSRegistryTool,
        tools.JSRegistry.JSRegistryTool,
    )

    ToolInit(
        config.PROJECTNAME + ' Tool',
        tools = TOOLS,
        product_name = config.PROJECTNAME,
        icon = 'tool.gif',
    ).initialize(context)
