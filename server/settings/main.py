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
from .create_plugins import CreatorPluginsSettings, DEFAULT_CREATE_SETTINGS
from .templated_workfile_build import TemplatedWorkfileBuildModel


class GafferSettings(BaseSettingsModel):
    imageio: ImageIOSettings = SettingsField(
        default_factory=ImageIOSettings, title="Color Management (imageio)")
    load: LoaderPluginsModel = SettingsField(
        default_factory=LoaderPluginsModel,
        title="Loader Plugins")
    create: CreatorPluginsSettings = SettingsField(
        default_factory=CreatorPluginsSettings,
        title="Creator Plugins")
    node_preset_paths: list[str] = SettingsField(
        default_factory=list,
        title="Node preset paths"
    )
    deadline: GafferDeadlineSettings = SettingsField(
        default_factory=GafferDeadlineSettings,
        title="Deadline"
    )
    templated_workfile_build: TemplatedWorkfileBuildModel = SettingsField(
        title="Templated Workfile Build",
        default_factory=TemplatedWorkfileBuildModel
    )


DEFAULT_VALUES = {
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "load": DEFAULT_LOADER_PLUGINS_SETTINGS,
    "node_preset_paths": [],
    "deadline": DEFAULT_DEADLINE_SETTINGS,
    "create": DEFAULT_CREATE_SETTINGS,
    "templated_workfile_build": {"profiles": []},
}
