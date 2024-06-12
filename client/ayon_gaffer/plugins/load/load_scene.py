from ayon_core.pipeline import (
    load,
    get_representation_path,
)

from ayon_gaffer.api import get_root, imprint_container
from ayon_gaffer.api.lib import set_node_color

import GafferScene


class GafferLoadScene(load.LoaderPlugin):
    """Load Scene"""

    product_types = ["pointcache", "model", "usd", "look", "animation", "layout"]
    representations = ["abc", "usd"]

    label = "Load scene"
    order = -10
    icon = "code-fork"
    color = "orange"

    node_name_template = "{folder[fullname]}"

    def load(self, context, name, namespace, data):
        # Create the Loader with the filename path set
        script = get_root()
        node = GafferScene.SceneReader()

        folder = context["folder"]
        folder_name = folder["name"]

        node.setName(self._get_node_name(context))

        path = self.filepath_from_context(context).replace("\\", "/")
        node["fileName"].setValue(path)
        script.addChild(node)

        # Colorize based on family
        # TODO: Use settings instead
        set_node_color(node, (0.369, 0.82, 0.118))

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
        try:
            from ayon_core.pipeline.template_data import (
                construct_folder_full_name
            )
            use_full_name = True
        except ModuleNotFoundError:
            # couldn't load the rvx custom core function
            use_full_name = False
        folder_entity = context["folder"]
        product_name = context["product"]["name"]
        repre_entity = context["representation"]

        folder_name = folder_entity["name"]
        hierarchy_parts = folder_entity["path"].split("/")
        hierarchy_parts.pop(0)
        if use_full_name:
            full_name = construct_folder_full_name(
                context["project"]["name"], folder_entity, hierarchy_parts)
        else:
            full_name = folder_name
        repre_cont = repre_entity["context"]
        name_data = {
            "folder": {
                "name": folder_name,
                "fullname": full_name
            },
            "product": {
                "name": product_name,
            },
            "asset": folder_name,
            "subset": product_name,
            "representation": repre_entity["name"],
            "ext": repre_cont["representation"],
            "id": repre_entity["id"],
            "class_name": self.__class__.__name__
        }

        return self.node_name_template.format(**name_data)
