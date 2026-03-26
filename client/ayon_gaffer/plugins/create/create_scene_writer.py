from ayon_core.lib import NumberDef
from ayon_gaffer.api import plugin

import Gaffer
import GafferScene


class CreateGafferPointcache(plugin.GafferCreatorBase):
    identifier = "io.ayon.creators.gaffer.pointcache"
    label = "Pointcache"
    product_type = "pointcache"
    product_base_type = "pointcache"
    description = "Scene writer to pointcache"
    icon = "gears"

    def _create_node(self,
                     product_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode,
                     instance=None) -> Gaffer.Node:
        node = GafferScene.SceneWriter(product_name)
        script.addChild(node)

        if len(self.selected_nodes) >= 1:
            node["in"].setInput(self.selected_nodes[0]["out"])

        return node

    def get_instance_attr_defs(self):
        task_entity = self.create_context.get_current_folder_entity()
        frame_start = task_entity["attrib"]["frameStart"]
        frame_end = task_entity["attrib"]["frameEnd"]

        return [
            NumberDef("frameStart",
                      label="Frame Start",
                      default=frame_start,
                      decimals=0),
            NumberDef("frameEnd",
                      label="Frame End",
                      default=frame_end,
                      decimals=0),
        ]
