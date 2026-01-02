from __future__ import annotations

from typing import Any

from ayon_core.pipeline import InventoryAction


class LockVersions(InventoryAction):
    label = "Lock versions"
    icon = "lock"
    color = "#ffffff"
    order = -1

    @staticmethod
    def is_compatible(container: dict[str, Any]) -> bool:
        return container.get("version_locked") is not True

    def process(self, containers: list[dict[str, Any]]) -> bool:
        self.log.info('prcessing!')
        for container in containers:
            print("!!!", container)
            if container.get("version_locked") is True:
                continue
            key = "version_locked"
            node = container["_node"]
            if key in node["user"]:
                # revert the value
                value = node["user"][key].getValue()
                node["user"][key].setValue(not value)
            else:
                # we need to create it
                import Gaffer
                plug = Gaffer.BoolPlug(
                    key,
                    defaultValue=False,
                    flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
                    )
                plug.setValue(True)
                Gaffer.Metadata.registerValue(
                    plug, "layout:section", "Ayon")

                node["user"].addChild(plug)
        return True


class UnlockVersions(InventoryAction):
    label = "Unlock versions"
    icon = "lock-open"
    color = "#ffffff"
    order = -1

    @staticmethod
    def is_compatible(container: dict[str, Any]) -> bool:
        return container.get("version_locked") is True

    def process(self, containers: list[dict[str, Any]]) -> bool:
        for container in containers:
            if container.get("version_locked") is not True:
                continue
            node = container["_node"]
            key = "version_locked"
            if key in node["user"].keys():
                node["user"][key].setValue(False)
        return True
