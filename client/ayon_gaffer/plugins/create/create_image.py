from ayon_gaffer.api import plugin

import Gaffer
import GafferImage


class CreateGafferImage(plugin.GafferCreatorBase):
    identifier = "io.openpype.creators.gaffer.image"
    label = "Image"
    family = "image"
    description = "Image writer"
    icon = "fa5.eye"

    def _create_node(self,
                     subset_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:
        node = GafferImage.ImageWriter(subset_name)
        script.addChild(node)
        return node
