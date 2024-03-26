from ayon_gaffer.api import plugin

import Gaffer
import GafferScene


class CreateGafferPointcache(plugin.GafferCreatorBase):
    identifier = "io.openpype.creators.gaffer.pointcache"
    label = "Pointcache"
    family = "pointcache"
    description = "Scene writer to pointcache"
    icon = "gears"

    def _create_node(self,
                     subset_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:
        node = GafferScene.SceneWriter(subset_name)
        script.addChild(node)
        return node
