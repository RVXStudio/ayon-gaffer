from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
)

from .loader_plugins import (
    LoaderPluginsModel,
    DEFAULT_LOADER_PLUGINS_SETTINGS
)

from .imageio import ImageIOSettings, DEFAULT_IMAGEIO_SETTINGS
from .deadline import GafferDeadlineSettings, DEFAULT_DEADLINE_SETTINGS


class GafferSettings(BaseSettingsModel):
    imageio: ImageIOSettings = SettingsField(
        default_factory=ImageIOSettings, title="Color Management (imageio)")
    load: LoaderPluginsModel = SettingsField(
        default_factory=LoaderPluginsModel,
        title="Loader Plugins")
    node_preset_paths: list[str] = SettingsField(
        default_factory=list,
        title="Node preset paths"
    )
    deadline: GafferDeadlineSettings = SettingsField(
        default_factory=GafferDeadlineSettings,
        title="Deadline"
    )


DEFAULT_VALUES = {
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "load": DEFAULT_LOADER_PLUGINS_SETTINGS,
    "node_preset_paths": [],
    "deadline": DEFAULT_DEADLINE_SETTINGS,
}
