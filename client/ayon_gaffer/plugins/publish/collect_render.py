import re
import pyblish.api
import os
import Gaffer
import IECore
from openpype.lib import get_formatted_current_time
from openpype.hosts.gaffer.api.colorspace import ARenderProduct
from openpype.hosts.gaffer.api.lib import get_color_management_preferences


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
            ctxt["render:shot"] = instance.data["asset"].split("/")[-1]
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
            if frame_range == 'start_end':
                frames = [gctxt_start_frame, gctxt_end_frame]
            elif frame_range == 'custom':
                frames = IECore.FrameList.parse(
                    layer['custom_frames'].getValue()
                ).asList()
            else:
                frames = IECore.FrameList.parse(
                    f'{gctxt_start_frame}-{gctxt_end_frame}'
                ).asList()
            self.log.info(f"layer: {layer_name}: {outputs}")

            expected_files = {}
            for aov, path in outputs.items():
                file_list = []
                for frame in frames:
                    file_list.append(path % frame)
                expected_files[aov] = file_list

            colorspace_data = get_color_management_preferences(
                layer.scriptNode())
            # add the cleanup dirs to the instance, if it is not already there
            current_cleanupFullPaths = instance.data.get(
                "explicit_cleanup_dirs", [])

            cleanup_dirs = [os.path.normpath(ctxt.substitute(val)) for val
                            in layer["cleanup_paths"].getValue()]
            self.log.info(f"Found cleanup dirs {cleanup_dirs}")
            for cleandir in cleanup_dirs:
                if cleandir not in current_cleanupFullPaths:
                    self.log.info(f"Adding [{cleandir}] to"
                                  "instance.data['explicit_cleanup_dirs']")
                    current_cleanupFullPaths.append(cleandir)
                else:
                    self.log.info(f"Not adding [{cleandir}] to"
                                  "farm_cleanupFullPaths, it is already there")
            instance.data["explicit_cleanup_dirs"] = current_cleanupFullPaths

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
            "outputDir": output_dir
        }
        label = "{0} ({1})".format(layer_name, instance.data["asset"])
        label += "  [{0}-{1}]".format(
            int(data["frameStart"]), int(data["frameEnd"])
        )
        data["label"] = label
        instance.data.update(data)

    def create_generic_path(self, in_path):
        return re.sub(self._frame_expression, r'\1%04d\2', in_path)