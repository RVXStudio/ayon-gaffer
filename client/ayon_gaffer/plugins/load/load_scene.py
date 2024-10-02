from ayon_core.pipeline import (
    load,
    get_representation_path,
    get_current_context
)
from ayon_core.lib import filter_profiles

from ayon_gaffer.api import get_root, imprint_container
import ayon_gaffer.api.lib


class GafferLoadScene(load.LoaderPlugin):
    """Load Scene"""

    product_types = [
        "pointcache",
        "model",
        "usd",
        "look",
        "animation",
        "layout"
    ]
    representations = ["abc", "usd"]

    label = "Load scene"
    order = -10
    icon = "code-fork"
    color = "orange"

    node_name_template = "{folder[name]}"

    def load(self, context, name, namespace, data):
        # Create the Loader with the filename path set

        script = get_root()

        product_type = context["product"]["productType"]
        task_name = get_current_context()["task_name"]
        selected_profile = filter_profiles(
            self.template_profiles,  # these values come from the settings
            {'product_type': product_type, 'task_name': task_name},
            keys_order=['product_type', 'task_name'])

        if selected_profile is None:
            raise RuntimeError("No profile matches product_type: "
                               f"{product_type} and task_name: {task_name}!")

        node_name = selected_profile["node_name_template"]
        resolved_node_name = self._get_node_name(node_name, context)
        sg_location_template = selected_profile["scenegraph_location_template"]
        aux_transforms = selected_profile["auxiliary_transforms"]
        node = ayon_gaffer.api.lib.make_scene_load_box(
            script,
            resolved_node_name,
            sg_location_template,
            aux_transforms
        )

        # folder = context["folder"]

        # node.setName(self._get_node_name(context))

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

    def switch(self, container, context):
        self.update(container, context)

    def update(self, container, context):
        representation = context["representation"]
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

    def _get_node_name(self, node_name, context):
        return ayon_gaffer.api.lib.node_name_from_template(
            node_name, context)
