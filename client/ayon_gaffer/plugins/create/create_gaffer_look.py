from ayon_gaffer.api import plugin

import Gaffer
import GafferScene


class CreateGafferLook(plugin.GafferCreatorBase):
    identifier = "io.ayon.creators.gaffer.look"
    label = "Look (experimental; just USD)"
    product_type = "look"
    description = "Scene writer to look"
    icon = "gears"

    def _create_node(self,
                     product_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:
        node = GafferScene.SceneWriter(product_name)
        script.addChild(node)
        if len(self.selected_nodes) > 1:
            mnode = GafferScene.MergeScenes()
            script.addChild(mnode)
            for idx, snode in enumerate([n for n in self.selected_nodes]):
                mnode["in"][f"in{idx}"].setInput(snode["out"])
            node["in"].setInput(mnode["out"])
        elif len(self.selected_nodes) == 1:
            node["in"].setInput(self.selected_nodes[0]["out"])

        return node
