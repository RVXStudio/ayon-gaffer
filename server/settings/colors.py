from pydantic import validator
from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
    ensure_unique_names,
)
from ayon_server.types import ColorRGB_float

class PackageColorModel(BaseSettingsModel):
    _layout = "compact"
    package_name: str = SettingsField("", title="Package name", description="The package to colorize e.g. GafferArnold or GafferScene or straight up Gaffer")
    color: ColorRGB_float = SettingsField(
        title="Color"
    )
    


class NodeColorModel(BaseSettingsModel):
    _layout = "compact"
    color: ColorRGB_float = SettingsField(
        title="Color"
    )
    node_classes: list[str] = SettingsField("", title="Node class", description="The class name of the node you want to change the default color of, e.g. GafferImage.Clamp, this value overrides the package colors above")


class NodeColorSettings(BaseSettingsModel):
    """Gaffer node default colors settings."""

    packages: list[PackageColorModel] = SettingsField(
        title="Package coloring", 
        default_factory=list
    )
    nodes: list[NodeColorModel] = SettingsField(
        title="Node colors",
        default_factory=list
    )
    
DEFAULT_COLOR_SETTINGS = {
    "packages": [],
    "nodes": []
}
