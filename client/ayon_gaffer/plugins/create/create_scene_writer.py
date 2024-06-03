from ayon_gaffer.api import plugin

import Gaffer
import GafferScene


class CreateGafferPointcache(plugin.GafferCreatorBase):
    identifier = "io.ayon.creators.gaffer.pointcache"
    label = "Pointcache"
    product_type = "pointcache"
    description = "Scene writer to pointcache"
    icon = "gears"

    def _create_node(self,
                     product_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:
        node = GafferScene.SceneWriter(product_name)
        script.addChild(node)
        return node
