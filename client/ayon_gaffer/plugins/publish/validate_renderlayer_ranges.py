import IECore

from pyblish.api import InstancePlugin, ValidatorOrder

from ayon_core.pipeline import OptionalPyblishPluginMixin, PublishValidationError
import ayon_gaffer.api.utils


class ValidateRenderlayerRanges(InstancePlugin, OptionalPyblishPluginMixin):

    families = ["render"]
    hosts = ["gaffer"]
    label = "Validate Renderlayer Ranges"
    order = ValidatorOrder + 0.1
    optional = True

    def process(self, instance):
        if not self.is_active(instance.data):
            return
        node = instance.data["transientData"]["node"]
        try:
            frame_range = ayon_gaffer.api.utils.get_render_layer_range(
                node
            )
        except RuntimeError as err:
            raise PublishValidationError(err)
        except ValueError as err:
            self.log.warning(str(err))
            return
        frame_start, frame_end = frame_range

        folder_a = instance.data["folderEntity"]["attrib"]
        folder_frame_start = folder_a["frameStart"] - folder_a["handleStart"]
        folder_frame_end = folder_a["frameEnd"] + folder_a["handleEnd"]

        if (folder_frame_start != frame_start or
                folder_frame_end != frame_end):

            folder_range = f"{folder_frame_start}-{folder_frame_end}"
            layer_range = f"{frame_start}-{frame_end}"
            raise PublishValidationError("Layer frame range does not match"
                f" folder range; folder: [{folder_range}],"
                f"layer: [{layer_range}]"
            )
