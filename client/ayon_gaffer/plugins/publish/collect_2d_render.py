import re
import pyblish.api
import os
import Gaffer
import IECore
from ayon_core.pipeline import publish

from ayon_core.lib import get_formatted_current_time
from ayon_gaffer.api.colorspace import ARenderProduct
from ayon_gaffer.api.lib import get_color_management_preferences


class Collect2DRender(pyblish.api.InstancePlugin):
    """Collect current Gaffer script"""

    order = pyblish.api.CollectorOrder
    label = "Collect render 2d"
    hosts = ["gaffer"]
    families = ["render2d"]


    def process(self, instance):
        context = instance.context

        render_node = instance.data.get("transientData", {}).get("node", None)
        if not render_node:
            raise RuntimeError("Unable to find the 2d render node")
        self.log.debug(f"Using node: {render_node.getName()}")

        scene_path = context.data["currentFile"].replace("\\", "/")

        img_seq_filepath = render_node["fileName"].getValue()
        dirname = os.path.dirname(img_seq_filepath)
        start_frame = render_node["startFrame"].getValue()
        end_frame = render_node["endFrame"].getValue()
        files = [os.path.basename(img_seq_filepath.replace("####", f"{x:04d}")) for x in range(start_frame, end_frame + 1)]
        frames = list(range(start_frame, end_frame + 1))
        if "representations" not in instance.data:
            instance.data["representations"] = []

        colorspace_data = get_color_management_preferences(render_node.scriptNode())

        data = {
            "farm": True,

            "attachTo": [],

            "multipartExr": True,

            "handleStart": 0,
            "handleEnd": 0,
            "frameStart": end_frame,
            "frameEnd": start_frame,
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

        # todo change label, is it the deadline job name?
        label = "{0} ({1})".format("render2D", instance.data["folderPath"])
        label += "  [{0}-{1}]".format(start_frame, end_frame)

        data["label"] = label
        instance.data.update(data)

        instance.data["families"].append("render.farm")
