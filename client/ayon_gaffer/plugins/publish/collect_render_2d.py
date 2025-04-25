import pyblish.api
import os
import Gaffer
import IECore

from ayon_core.lib import get_formatted_current_time
from ayon_gaffer.api.colorspace import ARenderProduct
from ayon_gaffer.api.lib import get_color_management_preferences


class CollectRender2D(pyblish.api.InstancePlugin):
    """Collect current Gaffer script"""

    order = pyblish.api.CollectorOrder
    label = "Collect render 2d"
    hosts = ["gaffer"]
    families = ["render"]


    def process(self, instance):
        context = instance.context
        render_node = instance.data.get("transientData", {}).get("node", None)
        if not render_node:
            raise RuntimeError("Unable to find the 2d render node")
        if render_node.typeName() != "AyonGaffer::Render2D":
            self.log.debug(f"Skip collecting node, not a Render2D node, type is {render_node.typeName()}")
            return
        self.log.debug(f"Using node: {render_node.getName()}")

        scene_path = context.data["currentFile"].replace("\\", "/")

        img_seq_filepath = render_node["fileName"].getValue()
        dirname = os.path.dirname(img_seq_filepath)
        start_frame = render_node["startFrame"].getValue()
        end_frame = render_node["endFrame"].getValue()
        file_paths = [img_seq_filepath.replace("####", f"{x:04d}") for x in range(start_frame, end_frame + 1)]
        files = [os.path.basename(x) for x in file_paths]
        frames = list(range(start_frame, end_frame + 1))

        colorspace_data = get_color_management_preferences(render_node.scriptNode())

        data = {

            "attachTo": [],

            "multipartExr": True,

            "handleStart": 0,
            "handleEnd": 0,
            "frameStart": start_frame,
            "frameEnd": end_frame,
            "frameStartHandle": 0,
            "frameEndHandle": 0,
            "frameList": frames,
            "byFrameStep": 1,
            "expectedFiles": [{"beauty": files}],

            "colorspaceConfig": colorspace_data["config"],
            "colorspaceDisplay": colorspace_data["display"],
            "colorspaceView": colorspace_data["view"],
            "colorspace": colorspace_data["colorspace"],

            "time": get_formatted_current_time(),
            "author": context.data["user"],

            "outputDir": dirname,
            "stagingDir": dirname,
            "source": scene_path,
            "renderProducts": ARenderProduct(render_node.scriptNode(), ["beauty"]),

            # this utilizes an RVX modification to the publishing process
            # where we can enable/disable hardlinking when instances
            # request it
            "do_hardlink": True
        }

        render_target = instance.data["creator_attributes"]["render_target"]

        if render_target == "frames":  # use existing frames for local publish
            self.log.debug("Using existing frames for local publish")
            if "representations" not in data:
                data["representations"] = []
            data["representations"].append({
                'name': "exr",
                'ext': "exr",
                'files': files,
                "stagingDir": dirname,
            })

        elif render_target == "frames_farm": # use existing frames for publish on farm
            self.log.debug("Using existing frames for farm publish")

            if "representations" not in data:
                data["representations"] = []

            data["representations"].append({
                'name': "exr",
                'ext': "exr",
                'files': files,
                "stagingDir": dirname,
            })

            data["expectedFiles"] = file_paths
            data["transfer"] = False
            data["farm"] = True
            instance.data["families"].append("render.frames_farm")

        elif render_target == "farm":  # render and publish on farm
            self.log.debug("Using farm for render and publish")
            data["farm"] = True
            instance.data["families"].append("render.farm")

        elif render_target == "local":  # render and publish locally
            self.log.debug("Using local for render and publish")
            instance.data["families"] = ["render.local"]

        # todo change label, is it the deadline job name?
        label = "{0} ({1})".format("render", instance.data["folderPath"])
        label += "  [{0}-{1}]".format(start_frame, end_frame)

        data["label"] = label
        instance.data.update(data)

