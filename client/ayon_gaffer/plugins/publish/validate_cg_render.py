from pyblish.api import InstancePlugin, ValidatorOrder

from ayon_core.pipeline import AYONPyblishPluginMixin, PublishValidationError
from ayon_gaffer.api.utils import get_pyseq_sequence


class ValidateCGRender(InstancePlugin, AYONPyblishPluginMixin):

    families = ["render"]
    hosts = ["gaffer"]
    label = "Validate CGRender"
    order = ValidatorOrder + 0.1
    optional = False

    def process(self, instance):
        cg_render_node = instance.data.get("transientData", {}).get("node", None)
        if not cg_render_node:
            raise RuntimeError("Unable to find the scene writer node")

        plug = cg_render_node["in"]

        if not plug.getInput():
            raise PublishValidationError(
                f"The scene writer '{cg_render_node.getName()}'"
                f"is not connected to any node.\n"
                f" Please connect it to the source of the camera you want to publish"
            )
        file_path = cg_render_node["fileName"].getValue()
        start_frame = cg_render_node["startFrame"].getValue()
        end_frame = cg_render_node["endFrame"].getValue()
        seq = get_pyseq_sequence(file_path)
        if not seq:
            raise PublishValidationError(
                f"Unable to find an image sequence on disk matching the file path '{file_path}'"
            )
        if start_frame != seq.start() or end_frame != seq.end():
            raise PublishValidationError(
                f"The start and end frame of the sequence '{seq}' "
                f"does not match the start and end frame of the scene writer node."
            )
        if seq.missing():
            raise PublishValidationError(
                f"The image sequence '{seq}' is missing frames."
            )