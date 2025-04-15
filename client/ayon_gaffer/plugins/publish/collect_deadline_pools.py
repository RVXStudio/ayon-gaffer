# -*- coding: utf-8 -*-
import pyblish.api
from ayon_core.lib import TextDef, UILabelDef, NumberDef, UISeparatorDef
from ayon_core.pipeline.publish import AYONPyblishPluginMixin


class CollectGafferDeadlinePools(pyblish.api.InstancePlugin,
                                 AYONPyblishPluginMixin):
    order = pyblish.api.CollectorOrder + 0.421
    label = "Collect Gaffer Deadline Pools"
    hosts = ["gaffer"]

    families = ["render", "render2d"]

    primary_pool = None
    secondary_pool = None
    group = ""

    submission_defaults = {}
    gaffer_deadline_profiles = {}

    @classmethod
    def apply_settings(cls, project_settings):
        # deadline.publish.CollectDeadlinePools
        settings = project_settings["gaffer"]["deadline"]
        default_sub_settings = settings["default_submission_settings"]
        task_node_settings = settings["task_node_submission_settings"]

        settings_dict = {"default": default_sub_settings}
        for profile in task_node_settings:
            title = profile["label"]
            settings_dict[title] = profile["submission_settings"]

        cls.submission_defaults = settings_dict

        cls.gaffer_deadline_profiles = (project_settings["deadline"]["publish"]
                                        ["CollectJobInfo"]["profiles"])

    def process(self, instance):
        attr_values = self.get_attr_values_from_data(instance.data)

        deadline_submission_settings = {}
        # repackage the settings as a single dictionary
        for attr, value in attr_values.items():
            if attr.count("_") == 0:
                grp = "default"
                attribute = attr
                self.log.info("autodetecting grp/attribute!")
            else:
                grp, attribute = attr.split("_", 1)

            if grp not in deadline_submission_settings.keys():
                deadline_submission_settings[grp] = {}

            deadline_submission_settings[grp][attribute] = value

        self.log.info(f"Collected: {deadline_submission_settings}")

        instance.data["deadline_submission_settings"] = deadline_submission_settings

    @classmethod
    def get_attribute_defs(cls):
        defs = []

        for label, settings in cls.submission_defaults.items():
            defs.append(UILabelDef(label))
            defs.extend([
                TextDef(f"{label}_primary_pool",
                        label=f"Primary Pool ({label})",
                        default=settings["primary_pool"],
                        tooltip=f"Deadline primary pool"),
                TextDef(f"{label}_secondary_pool",
                        label=f"Secondary Pool ({label})",
                        default=settings["secondary_pool"],
                        tooltip=f"Deadline secondary pool"),
                TextDef(f"{label}_group",
                        label=f"Group ({label})",
                        default=settings["group"],
                        tooltip=f"Deadline group"),
                NumberDef(f"{label}_priority",
                          label=f"Priority ({label})",
                          default=settings["priority"],
                          tooltip=f"Deadline priority")
            ])
        defs.append(UISeparatorDef())
        return defs
