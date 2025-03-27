from pyblish.api import InstancePlugin, ValidatorOrder

from ayon_core.pipeline import AYONPyblishPluginMixin, PublishValidationError
from ayon_gaffer.api.lib import traverse_scene, find_camera_paths, find_leaf_paths


class ValidateCamera(InstancePlugin, AYONPyblishPluginMixin):

    families = ["camera"]
    hosts = ["gaffer"]
    label = "Validate Camera"
    order = ValidatorOrder + 0.1
    optional = False

    def process(self, instance):
        scene_writer_node = instance.data.get("transientData", {}).get("node", None)
        if not scene_writer_node:
            raise RuntimeError("Unable to find the scene writer node")

        plug = scene_writer_node["in"]

        if not plug.getInput():
            raise PublishValidationError(
                f"The scene writer '{scene_writer_node.getName()}'"
                f"is not connected to any node.\n"
                f" Please connect it to the source of the camera you want to publish"
            )

        leaf_paths = find_leaf_paths(plug)

        if len(leaf_paths) == 0:
            raise PublishValidationError(
                "There is no scene graph location.\n"
                "Please add a camera scene graph location to export"
            )

        elif len(leaf_paths) >= 2:
            raise PublishValidationError(
                "There is more than one scene graph location.\n"
                "There should be only one camera to export.\n"
                "Please isolate the camera you want to publish."
            )

        type_ = plug.object(leaf_paths[0]).typeName()
        if  type_ != "Camera":
            raise PublishValidationError(
                f"Unable to find a camera scene graph location."
                f"Found type: {type_}"
            )
