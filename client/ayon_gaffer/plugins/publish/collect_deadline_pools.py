# -*- coding: utf-8 -*-
import pyblish.api
from ayon_core.lib import TextDef
from ayon_core.pipeline.publish import AYONPyblishPluginMixin


class CollectGafferDeadlinePools(pyblish.api.InstancePlugin,
                                 AYONPyblishPluginMixin):
    order = pyblish.api.CollectorOrder + 0.420
    label = "Collect Gaffer Deadline Pools"
    hosts = ["gaffer"]

    families = ["render"]

    primary_pool = None
    secondary_pool = None
    group = ""

    @classmethod
    def apply_settings(cls, project_settings):
        # deadline.publish.CollectDeadlinePools
        settings = project_settings["gaffer"]["deadline"]["pools"]
        try:
            default_settings = (project_settings["deadline"]
                                ["publish"]
                                ["CollectDeadlinePools"])
        except KeyError:
            # we got no deadline settings?
            default_settings = {}

        cls.primary_pool = settings.get("primary_pool", None)
        if not cls.primary_pool:
            cls.primary_pool = default_settings.get("primary_pool", None)
        cls.secondary_pool = settings.get("secondary_pool", None)
        if not cls.secondary_pool:
            cls.secondary_pool = default_settings.get("secondary_pool", None)
        cls.group = settings.get("group", None)

    def process(self, instance):
        attr_values = self.get_attr_values_from_data(instance.data)
        if not instance.data.get("primaryPool"):
            instance.data["primaryPool"] = (
                attr_values.get("primaryPool") or self.primary_pool or "none"
            )

        self.log.info("Collected primaryPool "
                      f"[{instance.data['primaryPool']}]")

        if not instance.data.get("secondaryPool"):
            instance.data["secondaryPool"] = (
                attr_values.get("secondaryPool") or self.secondary_pool or "none"  # noqa
            )

        self.log.info("Collected secondaryPool "
                      f"[{instance.data['secondaryPool']}]")

        if not instance.data.get("group"):
            instance.data["group"] = (
                attr_values.get("group") or self.group or ""
            )
        self.log.info(f"Collected group [{instance.data['group']}]")

    @classmethod
    def get_attribute_defs(cls):
        # TODO: Preferably this would be an enum for the user
        #       but the Deadline server URL can be dynamic and
        #       can be set per render instance. Since get_attribute_defs
        #       can't be dynamic unfortunately EnumDef isn't possible (yet?)
        # pool_names = self.deadline_module.get_deadline_pools(deadline_url,
        #                                                      self.log)
        # secondary_pool_names = ["-"] + pool_names

        return [
            TextDef("primaryPool",
                    label="Primary Pool",
                    default=cls.primary_pool,
                    tooltip="Deadline primary pool"),
            TextDef("secondaryPool",
                    label="Secondary Pool",
                    default=cls.secondary_pool,
                    tooltip="Deadline secondary pool"),
            TextDef("group",
                    label="Group",
                    default=cls.group,
                    tooltip="Deadline group")
        ]
