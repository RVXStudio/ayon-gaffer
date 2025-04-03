from pyblish.api import InstancePlugin, ValidatorOrder

from ayon_core.pipeline import AYONPyblishPluginMixin, PublishValidationError
from ayon_gaffer.api.lib import find_leaf_paths


class ValidatePointCache(InstancePlugin, AYONPyblishPluginMixin):

    families = ["pointcache"]
    hosts = ["gaffer"]
    label = "Validate Point Cache"
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
                f" Please connect it to the source of the geometry you want to publish"
            )

        leaf_paths = find_leaf_paths(plug)

        if len(leaf_paths) == 0:
            raise PublishValidationError(
                "There is no scene graph location.\n"
                "Please add a geometry scene graph location to export"
            )
