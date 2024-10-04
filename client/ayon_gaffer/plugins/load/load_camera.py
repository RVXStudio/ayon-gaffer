from ayon_core.pipeline import (
    get_representation_path,
)
from ayon_gaffer.api import get_root, imprint_container
from ayon_gaffer.api.lib import (
    set_node_color_from_settings,
    arrange,
    make_box,
    find_camera_paths
)

import ayon_gaffer.api.plugin

import Gaffer
import GafferScene
import IECore


class GafferLoadAlembicCamera(ayon_gaffer.api.plugin.GafferLoaderBase):
    """Load Alembic Camera"""

    product_types = ["camera"]
    representations = ["abc"]

    label = "Load camera"
    order = -10
    icon = "code-fork"
    color = "orange"

    def load(self, context, name, namespace, data):
        # Create the Loader with the filename path set
        script = get_root()

        # Due to an open issue to be implemented for Alembic we need to
        # manually assign the camera into Gaffer's '__cameras' set. So for
        # now we encapsulate what's needed in a Box node to resolve that.
        # See: https://github.com/GafferHQ/gaffer/issues/3954
        box = make_box(name, inputs=[], outputs=["out"])
        reader = GafferScene.SceneReader()
        box.addChild(reader)

        create_set = GafferScene.Set("cameras_set")
        box.addChild(create_set)
        create_set["name"].setValue("__cameras")
        create_set["in"].setInput(reader["out"])

        path_filter = GafferScene.PathFilter("all")
        box.addChild(path_filter)

        create_set["filter"].setInput(path_filter["out"])

        box["BoxOut_out"]["in"].setInput(create_set["out"])

        script.addChild(box)

        # Promote the reader's filename directly to the box
        Gaffer.PlugAlgo.promote(reader["fileName"])

        # Set the filename
        path = self.filepath_from_context(context).replace("\\", "/")
        box["fileName"].setValue(path)

        # Find all cameras in the loaded scene
        cameras = find_camera_paths(reader["out"])
        if len(cameras) > 0:
            camera_filter = cameras
        else:
            camera_filter = ['*']
        path_filter["paths"].setValue(IECore.StringVectorData(camera_filter))

        # Layout the nodes within the box
        arrange(box.children(Gaffer.Node))

        # Colorize based on family
        # TODO: Use settings instead
        self.set_node_color(box, context)

        imprint_container(box,
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
