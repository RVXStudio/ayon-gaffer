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

    def load(self, context, name, namespace, data):
        # Create the Loader with the filename path set

        node = GafferImage.ImageReader()

        path = self.filepath_from_context(context)
        path = self._convert_path(path)
        node["fileName"].setValue(path)

        self.set_up_node(name, namespace, node, context)
        self.set_node_colorspace(
            node["colorSpace"],
            context,
            path)

    def update(self, container, context):
        representation = context["representation"]
        path = get_representation_path(representation)
        path = self._convert_path(path)

        node = container["_node"]
        node["fileName"].setValue(path)

        # Update the imprinted representation
        node["user"]["representation"].setValue(str(representation["id"]))

        self.set_node_colorspace(
            node["colorSpace"],
            context,
            path)
