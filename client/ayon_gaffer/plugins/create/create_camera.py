from ayon_core.lib import NumberDef
from ayon_gaffer.api import plugin

import Gaffer
import GafferScene


class CreateGafferCamera(plugin.GafferCreatorBase):
    identifier = "io.ayon.creators.gaffer.camera"
    label = "Camera"
    product_type = "camera"
    product_base_type = "camera"
    description = "Export animated camera"
    icon = "video-camera"

    def _create_node(self,
                     product_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:
        node = GafferScene.SceneWriter(product_name)
        script.addChild(node)

        if len(self.selected_nodes) >= 1:
            node["in"].setInput(self.selected_nodes[0]["out"])

        return node

    def get_instance_attr_defs(self):
        task_entity = self.create_context.get_current_folder_entity()
        frame_start = task_entity["attrib"]["frameStart"]
        frame_end = task_entity["attrib"]["frameEnd"]
        handle_start = task_entity["attrib"]["handleStart"]
        handle_end = task_entity["attrib"]["handleEnd"]

        return [
            NumberDef("frameStart",
                      label="Frame Start",
                      default=frame_start,
                      decimals=0),
            NumberDef("frameEnd",
                      label="Frame End",
                      default=frame_end,
                      decimals=0),
            NumberDef("handleStart",
                      label="Handle Start",
                      default=handle_start,
                      decimals=0),
            NumberDef("handleEnd",
                      label="Handle End",
                      default=handle_end,
                      decimals=0),
        ]
