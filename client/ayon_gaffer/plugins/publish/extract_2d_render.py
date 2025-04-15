import os

from ayon_core.pipeline import publish
from ayon_gaffer.api.plugin import GafferExtractorPlugin

class Extract2DRender(GafferExtractorPlugin, publish.OptionalPyblishPluginMixin):
    label = "Extract 2D Render"
    hosts = ["gaffer"]
    families = ["render2d.local"]
    representations = ["exr"]

    def process(self, instance):
        render_node = instance.data.get("transientData", {}).get("node", None)
        if not render_node:
            raise RuntimeError("Unable to find the 2d render node")
        self.log.debug(f"Using node: {render_node.getName()}")


        # todo here is mode frame of the render_target
        # todo do the others modes as well
        file_path = render_node["fileName"].getValue()
        dirname = os.path.dirname(file_path)
        start_frame = render_node["startFrame"].getValue()
        end_frame = render_node["endFrame"].getValue()
        files = [os.path.basename(file_path.replace("####", f"{x:04d}")) for x in range(start_frame, end_frame + 1)]
        if "representations" not in instance.data:
            instance.data["representations"] = []

        instance.data["representations"].append({
            'name': self.representations[0],
            'ext': self.representations[0],
            'files': files,
            "stagingDir": dirname,
        })
        #
        # render_target = instance.data["render_target"]
        #
        # # if render_target == "frames":
        # #     self._set_existing_files_data(instance, colorspace)
        #
        # # elif render_target == "frames_farm":
        # #     collected_frames = self._set_existing_files_data(
        # #         instance, colorspace)
        # #
        # #     self._set_expected_files(instance, collected_frames)
        # #
        # #     self._add_farm_instance_data(instance)
        #
        # if render_target == "farm":
        #     print("toto\n\n farm")
        #     instance.data.update({
        #         "transfer": False,
        #         "farm": True  # to skip integrate
        #     })
        #     self.log.info("Farm rendering ON ...")
