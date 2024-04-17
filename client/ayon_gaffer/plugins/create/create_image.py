from ayon_gaffer.api import plugin

import Gaffer
import GafferImage


class CreateGafferImage(plugin.GafferCreatorBase):
    identifier = "io.ayon.creators.gaffer.image"
    label = "Image"
    product_type = "image"
    description = "Image writer"
    icon = "fa5.eye"

    def _create_node(self,
                     product_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:
        node = GafferImage.ImageWriter(product_name)
        script.addChild(node)
        return node
