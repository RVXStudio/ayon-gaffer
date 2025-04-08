from ayon_gaffer.api import plugin
from ayon_core.lib import (
    BoolDef
)

import Gaffer
from ayon_gaffer.api.nodes.render_2d import RenderNode2D


class CreateGafferCGRender(plugin.GafferRenderCreator):
    identifier = "io.ayon.creators.gaffer.2drender"
    deprecated_identifiers = ["io.openpype.creators.gaffer.cgrender"]
    label = "2DRender"
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
        # todo I need to load the box with the imagewriter inside here.
        node = RenderNode2D(product_name)

        script.addChild(node)
        return node
