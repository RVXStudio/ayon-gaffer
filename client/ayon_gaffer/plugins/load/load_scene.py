from ayon_core.pipeline import (
    load,
    get_representation_path,
)

from ayon_gaffer.api import get_root, imprint_container
import ayon_gaffer.api.lib

import GafferScene


class GafferLoadScene(load.LoaderPlugin):
    """Load Scene"""

    product_types = ["pointcache", "model", "usd", "look", "animation", "layout"]
    representations = ["abc", "usd"]

    label = "Load scene"
    order = -10
    icon = "code-fork"
    color = "orange"

    node_name_template = "{folder[name]}"

    def load(self, context, name, namespace, data):
        # Create the Loader with the filename path set

        script = get_root()
        node = GafferScene.SceneReader()

        # folder = context["folder"]

        node.setName(self._get_node_name(context))

        path = self.filepath_from_context(context).replace("\\", "/")
        node["fileName"].setValue(path)
        script.addChild(node)

        # Colorize based on family
        # TODO: Use settings instead
        ayon_gaffer.api.lib.set_node_color(node, (0.369, 0.82, 0.118))

        imprint_container(node,
                          name=name,
                          namespace=namespace,
                          context=context,
                          loader=self.__class__.__name__)

    def switch(self, container, representation):
        self.update(container, representation)

    def update(self, container, representation):
        representation = representation["representation"]
        path = get_representation_path(representation)
        path = path.replace("\\", "/")

        node = container["_node"]
        node["fileName"].setValue(path)

        # Update the imprinted representation
        node["user"]["representation"].setValue(str(representation["id"]))

    def remove(self, container):
        node = container["_node"]

        parent = node.parent()
        parent.removeChild(node)

    def _get_node_name(self, context):
        return ayon_gaffer.api.lib.node_name_from_template(
            self.node_name_template, context)
