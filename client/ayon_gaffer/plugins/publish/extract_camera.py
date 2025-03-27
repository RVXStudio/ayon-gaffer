import os
from ayon_core.pipeline import publish
from ayon_gaffer.api.plugin import GafferExtractorPlugin
import GafferDispatch
from ayon_gaffer.api import get_root

class ExtractGafferCameraUSD(GafferExtractorPlugin, publish.OptionalPyblishPluginMixin):
    label = "Extract Gaffer Camera"
    hosts = ["gaffer"]
    families = ["camera"]
    representations = ["abc", "usd"]

    def process(self, instance):
        scene_writer_node = instance.data.get("transientData", {}).get("node", None)
        if not scene_writer_node:
            raise RuntimeError("Unable to find the scene writer node")
        self.log.debug(f"Using node: {scene_writer_node.getName()}")

        dir_path = self.staging_dir(instance)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        root = get_root()
        attr = instance.data["creator_attributes"]
        start = attr.get("frameStart", root["frameRange"]["start"].getValue())
        end = attr.get("frameEnd", root["frameRange"]["end"].getValue())
        handle_start = attr.get("handleStart", 0)
        handle_end = attr.get("handleEnd", 0)

        start -= handle_start
        start = max(1, start)
        end += handle_end

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

            representation_results.append({
                'name': rep,
                'ext': rep,
                'files': filename,
                "stagingDir": dir_path,
            })

            self.log.debug("Extracted instance '{0}' to: {1}".format(
                instance.name, path))

        if "representations" not in instance.data:
            instance.data["representations"] = []

        instance.data["representations"].extend(representation_results)
