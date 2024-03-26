from openpype.hosts.gaffer.api import plugin
from openpype.lib import (
    BoolDef
)


import Gaffer
from openpype.hosts.gaffer.api.nodes import AyonPublishTask


class CreateGafferRender(plugin.GafferRenderCreator):
    identifier = "io.openpype.creators.gaffer.render"
    label = "Render"
    family = "render"
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
                     subset_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:
        node = AyonPublishTask(subset_name)
        script.addChild(node)
        return node
