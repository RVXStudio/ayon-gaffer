import re
import pyblish.api
import os
import Gaffer
import IECore
from ayon_core.pipeline import publish

from ayon_core.lib import get_formatted_current_time
from ayon_gaffer.api.colorspace import ARenderProduct
from ayon_gaffer.api.lib import get_color_management_preferences


class CollectRender(pyblish.api.InstancePlugin):
    """Collect current Gaffer script"""

    order = pyblish.api.CollectorOrder
    label = "Collect render"
    hosts = ["gaffer"]
    families = ["render"]

    # _frame_expression = re.compile(r'(.*\.)\d{4}(\.[\w]+)$')
    _frame_expression = re.compile(r'(.*\.)####(\.[\w]+)$')

    def process(self, instance):
        """Collect render outputs"""

        context = instance.context
        filepath = context.data["currentFile"].replace("\\", "/")

        layer = instance.data["transientData"]["node"]

        layer.update_outputs()

        with Gaffer.Context(layer.scriptNode().context()) as ctxt:
            ctxt["render:shot"] = instance.data["folderPath"].split("/")[-1]
            ctxt['layer_name'] = ctxt.substitute(
                layer["layer_name"].getValue())
            ctxt['layer_type'] = layer['layer_type'].getValue()
            layer_name = layer['layer_name'].getValue()
            layer_output_folder = ctxt.substitute(
                layer["layer_output_path"].getValue())
            ctxt['layer_output_path'] = layer_output_folder
            outputs = {}
            for outplug in layer['outputs'].children():
                aov_name = outplug["name"].getValue()
                aov_output_path = self.create_generic_path(
                    outplug["value"].getValue()
                )
                self.log.info(f"before {aov_output_path}")
                self.log.info(f"sub {ctxt.substitute(aov_output_path)}")
                outputs[aov_name] = os.path.normpath(
                    ctxt.substitute(aov_output_path))
            frame_range = layer['frame_range'].getValue()
            gctxt_start_frame = ctxt.get("frameRange:start")
            gctxt_end_frame = ctxt.get("frameRange:end")
            if frame_range in ["start_end", "first_last"]:
                frames = [gctxt_start_frame, gctxt_end_frame]
            elif frame_range == "custom":
                frames = IECore.FrameList.parse(
                    layer["custom_frames"].getValue()
                ).asList()
            elif frame_range in ["timeline", "full_range"]:
                frames = IECore.FrameList.parse(
                    f'{gctxt_start_frame}-{gctxt_end_frame}'
                ).asList()
            elif frame_range == "layer_range":
                lr_start_frame = layer["layer_range"]["x"].getValue()
                lr_end_frame = layer["layer_range"]["y"].getValue()
                frames = IECore.FrameList.parse(
                    f"{lr_start_frame}-{lr_end_frame}"
                ).asList()
            else:
                raise publish.KnownPublishError(
                    f"unknown frame range value [{frame_range}] encountered")
            self.log.info(f"layer frames [{layer_name}]: {frames}")
            self.log.info(f"layer: {layer_name}: {outputs}")

            expected_files = {}
            for aov, path in outputs.items():
                file_list = []
                for frame in frames:
                    file_list.append(path % frame)
                expected_files[aov] = file_list

            colorspace_data = get_color_management_preferences(
                layer.scriptNode())

            # this is where the metadata json file will be placed at
            # now we construct the path to the gaffer_cleanup.json
            # add the cleanup dirs to the instance, if it is not already there

            cleanup_paths = [os.path.normpath(ctxt.substitute(val)) for val
                             in layer["cleanup_paths"].getValue()]
            self.log.info(f"Found cleanup dirs {cleanup_paths}")

            cleanup_file = os.path.join(
                layer_output_folder, "gaffer_cleanup.json")
            self.log.info(f"Path to cleanup file: {cleanup_file}")

            cleanup_paths.append(cleanup_file)

        output_dir = os.path.dirname(outputs[list(outputs.keys())[0]])

        data = {
            "farm": True,
            "attachTo": [],

            "multipartExr": True,
            "review": instance.data.get("review") or False,

            # Frame range
            "handleStart": 0,
            "handleEnd": 0,
            "frameStart": frames[0],
            "frameEnd": frames[-1],
            "frameStartHandle": 0,
            "frameEndHandle": 0,
            "frameList": frames,
            "byFrameStep": 1,

            "renderlayer": layer_name,
            "stagingDir": layer_output_folder,
            # todo: is `time` and `author` still needed?
            "time": get_formatted_current_time(),
            "author": context.data["user"],

            # Add source to allow tracing back to the scene from
            # which was submitted originally
            "source": filepath,
            "expectedFiles": [expected_files],
            # "publishRenderMetadataFolder": common_publish_meta_path,
            "renderProducts": ARenderProduct(layer.scriptNode()),
            "colorspaceConfig": colorspace_data["config"],
            "colorspaceDisplay": colorspace_data["display"],
            "colorspaceView": colorspace_data["view"],
            "outputDir": output_dir,
            "gaffer_cleanup_paths": cleanup_paths,
            "gaffer_cleanup_file_path": cleanup_file,
            # this utilizes an RVX modification to the publishing process
            # where we can enable/disable hardlinking when integrating
            # for certain cases
            "do_hardlink": True
        }
        label = "{0} ({1})".format(layer_name, instance.data["folderPath"])
        label += "  [{0}-{1}]".format(
            int(data["frameStart"]), int(data["frameEnd"])
        )
        data["label"] = label
        instance.data.update(data)

        instance.data["families"].append("render.farm")

    def create_generic_path(self, in_path):
        return re.sub(self._frame_expression, r'\1%04d\2', in_path)
