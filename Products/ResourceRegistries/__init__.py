from Products.CMFCore.utils import ToolInit
from Products.ResourceRegistries import config
from Products.ResourceRegistries.tools import CSSRegistry
from Products.ResourceRegistries.tools import JSRegistry
from Products.ResourceRegistries.tools import KSSRegistry


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
