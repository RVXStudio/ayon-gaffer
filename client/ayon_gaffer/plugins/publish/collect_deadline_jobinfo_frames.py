# -*- coding: utf-8 -*-
import pyblish.api
from ayon_core.lib import TextDef, UILabelDef, NumberDef, UISeparatorDef
from ayon_core.pipeline.publish import AYONPyblishPluginMixin


class CollectDeadlineJobInfoFrames(pyblish.api.InstancePlugin,
                                   AYONPyblishPluginMixin):
    order = pyblish.api.CollectorOrder + 0.43
    label = "Collect Deadline Job Info Frames"
    hosts = ["gaffer"]

    families = ["render"]

    def process(self, instance):
        job_info = instance.data.get("deadline", {}).get("job_info")

        if job_info is None:
            self.log.error(f"No deadline job info found!")
            return

        job_info.Frames = ",".join(
            [str(f) for f in instance.data["frameList"]])
