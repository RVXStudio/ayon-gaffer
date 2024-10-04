import os

from ayon_core.pipeline import (
    get_representation_path,
)
from ayon_gaffer.api import get_root, imprint_container
import ayon_gaffer.api.plugin


class GafferLoadArnoldVDB(ayon_gaffer.api.plugin.GafferLoaderBase):
    """Load VDB to Arnold"""

    product_types = ["vdbcache"]
    representations = ["vdb"]

    label = "Load VDB to Arnold"
    order = -10
    icon = "code-fork"
    color = "orange"

    def load(self, context, name, namespace, data):

        import GafferArnold

        # Create the Loader with the filename path set
        script = get_root()
        node = GafferArnold.ArnoldVDB()
        node.setName(name)

        path = self.filepath_from_context(context).replace("\\", "/")
        node["fileName"].setValue(path)
        script.addChild(node)

        self.set_node_color(node, context)

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


if not os.environ.get("ARNOLD_ROOT"):
    # Arnold not set up for Gaffer - exclude the loader
    del GafferLoadArnoldVDB
