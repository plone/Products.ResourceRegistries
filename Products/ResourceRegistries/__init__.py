from Products.CMFCore.utils import ToolInit

from Products.ResourceRegistries.tools import CSSRegistry, KSSRegistry, JSRegistry
from Products.ResourceRegistries import config

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
