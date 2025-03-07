from ayon_core.pipeline import InventoryAction
from ayon_core.tools.utils import host_tools

class ToggleVersionFreeze(InventoryAction):

    label = "Toggle version freeze"
    icon = "snowflake-o"
    color = "#d8d8d8"

    def process(self, containers):

        for container in containers:
            node = container["_node"]
            if "version_freeze" in node["user"]:
                # revert the value
                value = node["user"]["version_freeze"].getValue()
                print('got value', value)
                node["user"]["version_freeze"].setValue(not value)
            else:
                # we need to create it
                import Gaffer
                plug = Gaffer.BoolPlug(
                    "version_freeze",
                    defaultValue=False,
                    flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
                    )
                plug.setValue(True)
                Gaffer.Metadata.registerValue(
                    plug, "layout:section", "Ayon")

                node["user"].addChild(plug)
            h = host_tools.get_tool_by_name("sceneinventory")
            h.refresh()
