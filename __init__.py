from Products.CMFCore.utils import ToolInit

from Products.CSSRegistry.config import PROJECTNAME
from Products.CSSRegistry import tools

def initialize(context):

    TOOLS = (
        tools.CSSRegistry.CSSRegistryTool,
    )

    ToolInit(
        PROJECTNAME + ' Tool',
        tools = TOOLS,
        product_name = PROJECTNAME,
        icon = 'tool.gif',
    ).initialize(context)
