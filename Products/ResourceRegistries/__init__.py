from Products.CMFCore.utils import ToolInit
from Products.ResourceRegistries.config import PROJECTNAME
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
        PROJECTNAME + ' Tool',
        tools = TOOLS,
        icon = 'tool.gif',
    ).initialize(context)
