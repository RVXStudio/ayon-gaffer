from ayon_gaffer.api import plugin
from ayon_core.lib import (
    BoolDef
)


import Gaffer
from ayon_gaffer.api.nodes import AyonPublishTask


class CreateGafferRender(plugin.GafferRenderCreator):
    identifier = "io.ayon.creators.gaffer.render"
    label = "Render"
    product_type = "render"
    description = "Farm rendering"
    icon = "fa5.film"

    def get_instance_attr_defs(self):
        return [
            BoolDef(
                "farm_rendering",
                default=True,
                label="Farm rendering"
            )
        ]

    def _create_node(self,
                     product_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:
        node = AyonPublishTask(product_name)
        script.addChild(node)
        return node
