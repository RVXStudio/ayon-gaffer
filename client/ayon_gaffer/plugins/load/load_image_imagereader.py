import os

from ayon_core.pipeline import (
    load,
    get_representation_path,
)
from ayon_gaffer.api import get_root, imprint_container
import ayon_gaffer.api.lib
import ayon_gaffer.api.utils

import GafferImage


class GafferLoadImageReader(load.LoaderPlugin):
    """Load Image or Image sequence"""

    product_types = ["image", "imagesequence", "review", "render", "plate"]
    representations = ["*"]

    label = "Load sequence (ImageReader)"
    order = -10
    icon = "code-fork"
    color = "orange"

    def load(self, context, name, namespace, data):
        # Create the Loader with the filename path set
        script = get_root()
        node = GafferImage.ImageReader()
        node.setName(self._get_node_name(context))

        path = self.filepath_from_context(context)
        path = self._convert_path(path)
        node["fileName"].setValue(path)
        script.addChild(node)

        # Colorize based on family
        # TODO: Use settings instead
        ayon_gaffer.api.lib.set_node_color(node, (1, 0.98, 0.353))

        imprint_container(node,
                          name=name,
                          namespace=namespace,
                          context=context,
                          loader=self.__class__.__name__)

    def switch(self, container, representation):
        self.update(container, representation)

    def update(self, container, representation):

        path = get_representation_path(representation)
        path = self._convert_path(path)

        node = container["_node"]
        node["fileName"].setValue(path)

        # Update the imprinted representation
        node["user"]["representation"].setValue(str(representation["id"]))

    def remove(self, container):
        node = container["_node"]

        parent = node.parent()
        parent.removeChild(node)

    def _convert_path(self, path):
        # TODO: Actually detect whether it's a sequence. And support _ too.
        print('converting path', path)
        seq = ayon_gaffer.api.utils.get_pyseq_sequence(path)
        if len(seq) > 1:
            print("use #")
            padding = seq._get_padding()
            hash_padding = int(padding[1:-1])*"#"  # convert %04d to ####
            out_path = seq.format(f"%D%h{hash_padding}%t")
        else:
            out_path = seq.path()
        return out_path.replace("\\", "/")

    def _get_node_name(self, context):
        return ayon_gaffer.api.lib.node_name_from_template(
            self.node_name_template, context)
