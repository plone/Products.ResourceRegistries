from Products.CMFCore.utils import ToolInit
from Products.CMFCore.DirectoryView import registerDirectory

from Products.ResourceRegistries.tools import CSSRegistry, KSSRegistry, JSRegistry
from Products.ResourceRegistries import config

registerDirectory(config.SKINS_DIR, config.GLOBALS)

def initialize(context):

    TOOLS = (
        CSSRegistry.CSSRegistryTool,
        KSSRegistry.KSSRegistryTool,
        JSRegistry.JSRegistryTool,
    )

    ToolInit(
        config.PROJECTNAME + ' Tool',
        tools = TOOLS,
        icon = 'tool.gif',
    ).initialize(context)
