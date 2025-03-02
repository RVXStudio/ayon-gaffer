from ayon_core.pipeline import (
    get_representation_path,
)
from ayon_gaffer.api import get_root, imprint_container
import ayon_gaffer.api.plugin

import Gaffer


class GafferLoadReference(ayon_gaffer.api.plugin.GafferLoaderBase):
    """Reference a gaffer scene"""

    product_types = ["gafferNodes"]
    representations = ["gfr"]

    label = "Reference Gaffer Scene"
    order = -10
    icon = "code-fork"
    color = "orange"

    def load(self, context, name, namespace, data):

        script = get_root()

        path = self.filepath_from_context(context).replace("\\", "/")

        reference = Gaffer.Reference(name)
        script.addChild(reference)
        reference.load(path)

        self.set_node_color(reference, context)

        imprint_container(reference,
                          name=name,
                          namespace=namespace,
                          context=context,
                          loader=self.__class__.__name__)

    def switch(self, container, context):
        self.update(container, context)

    def update(self, container, context):
        path = get_representation_path(context["representation"])
        path = path.replace("\\", "/")

        # This is where things get tricky - do we just remove the node
        # completely and replace it with a new one? For now we do. Preferably
        # however we would have it like a 'reference' so that we can just
        # update the loaded 'box' or 'contents' to the new one.
        node: Gaffer.Reference = container["_node"]
        node.load(path)

        # Update the imprinted representation
        node["user"]["representation"].setValue(
            str(context["representation"]["id"]))

    def remove(self, container):
        node = container["_node"]

        parent = node.parent()
        parent.removeChild(node)
