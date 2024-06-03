import os
import re

import pyblish.api

from ayon_core.pipeline import publish


class ExtractGafferUSD(
    publish.Extractor,
    publish.OpenPypePyblishPluginMixin
):
    """Export Gaffer Scene Writer"""

    order = pyblish.api.ExtractorOrder
    label = "Extract Gaffer USD"
    hosts = ["gaffer"]
    families = ["model", "look"]

    def process(self, instance):

        node = instance.data["transientData"]["node"]

        staging_dir = self.staging_dir(instance)
        filename = "{0}.usd".format(instance.name)
        path = os.path.join(staging_dir, filename)

        original_filepath = node["fileName"].getValue()

        node["fileName"].setValue(path)

        if "#" in path:
            # Replace hash tokens (#) with frame number
            context = node.scriptNode().context()
            frame = context.getFrame()

            def fn(match):
                padding = len(match.group(0))
                return str(frame).zfill(padding)

            path = re.sub("(#+)", fn, path)

        # Export node
        # TODO: Support `executeSequence(frames: List[int])` to render sequence
        node.execute()

        # Add representation to instance
        ext = os.path.splitext(path)[-1].strip(".")
        representation = {
            "name": ext,
            "ext": ext,
            "files": os.path.basename(path),
            "stagingDir": os.path.dirname(path),
        }
        representations = instance.data.setdefault("representations", [])
        representations.append(representation)

        node["fileName"].setValue(original_filepath)
