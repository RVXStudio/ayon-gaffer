from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
)

from .loader_plugins import (
    LoaderPluginsModel,
    DEFAULT_LOADER_PLUGINS_SETTINGS
)

from .imageio import ImageIOSettings, DEFAULT_IMAGEIO_SETTINGS


class GafferDeadlineEnvVarModel(BaseSettingsModel):
    _layout = "expanded"
    name: str = SettingsField(
        title="Variable name"
    )
    use_env_value: bool = SettingsField(
        title="Copy value from environment"
    )
    value: str = SettingsField(
        title="Variable value"
    )


class GafferDeadlinePoolSettings(BaseSettingsModel):
    primary_pool: str = SettingsField(
        title="Primary Pool"
    )
    secondary_pool: str = SettingsField(
        title="Secondary Pool"
    )
    group: str = SettingsField(
        title="Group"
    )


class GafferDeadlineSettings(BaseSettingsModel):
    env_vars: list[GafferDeadlineEnvVarModel] = SettingsField(
        title="Environment variables",
        default_factory=list
    )
    pools: GafferDeadlinePoolSettings = SettingsField(
        default_factory=GafferDeadlinePoolSettings,
        title="Pools"
    )


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
        title="GafferDeadline"
    )


DEFAULT_VALUES = {
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "load": DEFAULT_LOADER_PLUGINS_SETTINGS,
    "node_preset_paths": [],
    "deadline": {
        "env_vars": [
            {"name": "ARNOLD_ROOT", "use_env_value": True, "value": ""},
            {
                "name": "GAFFER_EXTENSION_PATHS",
                "use_env_value": True, "value": ""
            },
            {"name": "AYON_APP_NAME", "use_env_value": True, "value": ""},
            {"name": "AYON_TASK_NAME", "use_env_value": True, "value": ""},
            {"name": "AYON_PROJECT_NAME", "use_env_value": True, "value": ""},
            {"name": "AYON_FOLDER_PATH", "use_env_value": True, "value": ""},
            {"name": "AYON_BUNDLE_NAME", "use_env_value": True, "value": ""},
            {"name": "AYON_RENDER_JOB", "use_env_value": False, "value": "1"},
        ],
        "pools": {
            "group": "",
            "primary_pool": "",
            "secondary_pool": "",
        }
    }
}
