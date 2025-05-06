from ayon_core.pipeline import (
    get_representation_path,
)
import ayon_gaffer.api.lib
import ayon_gaffer.api.utils
import ayon_gaffer.api.plugin

import GafferImage


class GafferLoadImageReader(ayon_gaffer.api.plugin.GafferImageLoaderBase):
    """Load ImageReader"""

    product_types = ["image", "imagesequence", "review", "render", "plate"]
    representations = ["*"]

    label = "Load sequence (ImageReader)"
    order = -10
    icon = "code-fork"
    color = "orange"

    def load(self, context, name, namespace, options):
        # Create the Loader with the filename path set

        node = GafferImage.ImageReader()

        # path = self.filepath_from_context(context)
        # path = self._convert_path(path, options)
        path = self.prepare_image_path(context, options)
        node["fileName"].setValue(path)

        self.set_up_node(name, namespace, node, context)
        self.set_node_colorspace(
            node["colorSpace"],
            context,
            path)

    def update(self, container, context):
        representation = context["representation"]
        node = container["_node"]
        path = self.prepare_image_path(context, node=node)

        node["fileName"].setValue(path)

        # Update the imprinted representation
        node["user"]["representation"].setValue(str(representation["id"]))

        self.set_node_colorspace(
            node["colorSpace"],
            context,
            path)
