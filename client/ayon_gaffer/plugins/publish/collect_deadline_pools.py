# -*- coding: utf-8 -*-
import pyblish.api
from ayon_core.lib import TextDef, UILabelDef, NumberDef, UISeparatorDef
from ayon_core.pipeline.publish import AYONPyblishPluginMixin
from ayon_core.lib.profiles_filtering import filter_profiles

from ayon_deadline.lib import AYONDeadlineJobInfo


class CollectGafferDeadlinePools(pyblish.api.InstancePlugin,
                                 AYONPyblishPluginMixin):
    order = pyblish.api.CollectorOrder + 0.421
    label = "Collect Gaffer Deadline Pools"
    hosts = ["gaffer"]

    families = ["render"]

    primary_pool = None
    secondary_pool = None
    group = ""

    submission_defaults = {}
    gaffer_deadline_profiles  = {}

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

        cls.gaffer_deadline_profiles = project_settings["deadline"]["publish"]["CollectJobInfo"]["profiles"]


    def process(self, instance):
        attr_values = self.get_attr_values_from_data(instance.data)

        deadline_submission_settings = {}
        # repackage the settings as a single dictionary
        for attr, value in attr_values.items():
            grp, attribute = attr.split("_", 1)

            if grp not in deadline_submission_settings.keys():
                deadline_submission_settings[grp] = {}

            deadline_submission_settings[grp][attribute] = value

        self.log.info(f"Collected: {deadline_submission_settings}")

        instance.data["deadline_submission_settings"] = deadline_submission_settings


    def _get_jobinfo_defaults(self, instance):
        """Queries project setting for profile with default values

        Args:
            instance (pyblish.api.Instance): Source instance.

        Returns:
            (dict)
        """
        context_data = instance.context.data
        host_name = context_data["hostName"]
        task_entity = context_data.get("taskEntity")

        task_name = task_type = None
        if task_entity:
            task_name = task_entity["name"]
            task_type = task_entity["taskType"]

        profile = filter_profiles(
            self.gaffer_deadline_profiles,
            {
                "host_names": host_name,
                "task_types": task_type,
                "task_names": task_name,
                # "product_type": product_type
            }
        )
        return profile or {}

    @classmethod
    def get_attribute_defs(cls):
        # TODO: Preferably this would be an enum for the user
        #       but the Deadline server URL can be dynamic and
        #       can be set per render instance. Since get_attribute_defs
        #       can't be dynamic unfortunately EnumDef isn't possible (yet?)
        # pool_names = self.deadline_module.get_deadline_pools(deadline_url,
        #                                                      self.log)
        # secondary_pool_names = ["-"] + pool_names

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
