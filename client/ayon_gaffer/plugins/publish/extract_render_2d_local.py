import os

import GafferDispatch
from ayon_core.pipeline import publish
from ayon_gaffer.api.plugin import GafferExtractorPlugin

class Extract2DRender(GafferExtractorPlugin, publish.OptionalPyblishPluginMixin):
    label = "Extract 2D Render"
    hosts = ["gaffer"]
    families = ["render.local"]
    representations = ["exr"]

    def process(self, instance):
        render_node = instance.data.get("transientData", {}).get("node", None)
        if not render_node:
            raise RuntimeError("Unable to find the 2d render node")
        self.log.debug(f"Using node: {render_node.getName()}")

        file_path = render_node["fileName"].getValue()
        dirname = os.path.dirname(file_path)
        start_frame = render_node["startFrame"].getValue()
        end_frame = render_node["endFrame"].getValue()
        files = [os.path.basename(file_path.replace("####", f"{x:04d}")) for x in range(start_frame, end_frame + 1)]

        dispatcher = GafferDispatch.LocalDispatcher()
        dispatcher["framesMode"].setValue(2)  # custom range
        # Set to full range does not work, we need to manually set the frame range by hand
        frange = f"{start_frame}-{end_frame}"
        self.log.debug(f"Using frame range: {frange}")
        dispatcher["frameRange"].setValue(frange)

        dispatcher.dispatch([render_node])

        if "representations" not in instance.data:
            instance.data["representations"] = []

        instance.data["representations"].append({
            'name': self.representations[0],
            'ext': self.representations[0],
            'files': files,
            "stagingDir": dirname,
        })

        families = instance.data["families"]
        if "render.local" in families:
            families.remove("render.local")
            families.insert(0, "render")