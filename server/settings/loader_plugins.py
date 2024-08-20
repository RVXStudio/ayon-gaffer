from pydantic import validator
from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
    ensure_unique_names
)

from .common import PlugModel


class LoadSceneModel(BaseSettingsModel):
    enabled: bool = SettingsField(
        title="Enabled"
    )

    node_name_template: str = SettingsField(
        title="SceneReader node name template"
    )


class LoadImageModel(BaseSettingsModel):
    enabled: bool = SettingsField(
        title="Enabled"
    )

    node_name_template: str = SettingsField(
        title="Node name template"
    )

    plugs: list[PlugModel] = SettingsField(
        default_factory=list,
        title="Plugs",
    )

    @validator("plugs")
    def ensure_unique_names(cls, value):
        """Ensure name fields within the lists have unique names."""
        ensure_unique_names(value)
        return value


class LoaderPluginsModel(BaseSettingsModel):
    GafferLoadScene: LoadSceneModel = SettingsField(
        default_factory=LoadSceneModel,
        title="Load Scene"
    )

    GafferLoadImageReader: LoadImageModel = SettingsField(
        default_factory=LoadImageModel,
        title="Load Image (ImageReader)"
    )

    GafferLoadImageAiImage: LoadImageModel = SettingsField(
        default_factory=LoadImageModel,
        title="Load Image (aiImage)"
    )


DEFAULT_LOADER_PLUGINS_SETTINGS = {
    "GafferLoadScene": {
        "enabled": True,
        "node_name_template": "{folder[name]}_{ext}"
    },
    "GafferLoadImageReader": {
        "enabled": True,
        "node_name_template": "{folder[name]}_{ext}",
        "plugs": [],
    },
    "GafferLoadImageAiImage": {
        "enabled": True,
        "node_name_template": "{folder[name]}_{ext}",
        "plugs": [],
    },
}
