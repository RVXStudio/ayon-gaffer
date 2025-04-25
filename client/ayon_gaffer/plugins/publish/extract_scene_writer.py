import os
import GafferDispatch

import pyblish.api
from ayon_core.lib import BoolDef
from ayon_core.pipeline import publish
from ayon_gaffer.api import get_root


class ExtractGafferSceneWriter(publish.Extractor, publish.AYONPyblishPluginMixin):
    """Export Gaffer Scene Writer"""

    order = pyblish.api.ExtractorOrder
    label = "Gaffer Scene Writer"
    hosts = ["gaffer"]
    families = ["pointcache"]
    representations = ["abc", "usd"]

    def process(self, instance):

        scene_writer_node = instance.data["transientData"]["node"]

        dir_path = self.staging_dir(instance)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        root = get_root()
        attr = instance.data["creator_attributes"]

        start = attr.get("frameStart", root["frameRange"]["start"].getValue())
        end = attr.get("frameEnd", root["frameRange"]["end"].getValue())

        include_handles = instance.data.get("publish_attributes", {}).get("ExtractGafferSceneWriter", {}).get(
            "includeHandles", False)

        if include_handles:
            self.log.debug("Including handles")

        if include_handles:
            start -= 1
            end += 1

        dispatcher = GafferDispatch.LocalDispatcher()
        dispatcher["framesMode"].setValue(2)  # custom range
        # Set to full range does not work, we need to manually set the frame range by hand
        frange = f"{start}-{end}"
        self.log.debug(f"Using frame range: {frange}")
        dispatcher["frameRange"].setValue(frange)

        representation_results = []
        for rep in self.representations:

            filename = "{}.{}".format(instance.name, rep)
            path = os.path.join(dir_path, filename)
            scene_writer_node["fileName"].setValue(path)
            dispatcher.dispatch([scene_writer_node])

            representation_results.append(
                {
                    "name": rep,
                    "ext": rep,
                    "files": filename,
                    "stagingDir": dir_path,
                }
            )

            self.log.debug("Extracted instance '{0}' to: {1}".format(instance.name, path))

        if "representations" not in instance.data:
            instance.data["representations"] = []

        instance.data["representations"].extend(representation_results)

    @classmethod
    def get_attribute_defs(cls):
        return [
            BoolDef("includeHandles",
                    label="Add Cache Handles",
                    tooltip="This will add one frame before and after for the motion blur",
                    default=True),
        ]