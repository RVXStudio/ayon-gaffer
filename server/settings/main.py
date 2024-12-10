from pydantic import validator
from ayon_server.exceptions import BadRequestException

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


class GafferDeadlineSubmissionSettings(BaseSettingsModel):
    priority: int = SettingsField(
        title="Priority",
        default_factory=int
    )
    primary_pool: str = SettingsField(
        title="Primary Pool",
        default_factory=str
    )
    secondary_pool: str = SettingsField(
        title="Secondary Pool",
        default_factory=str
    )
    group: str = SettingsField(
        title="Group",
        default_factory=str
    )


class GafferDeadlineSettingsNodetypeProfiles(BaseSettingsModel):
    _layout = "expanded"
    node_type: list[str] = SettingsField(
        title="Node types",
        default_factory=list
    )
    submission_settings: GafferDeadlineSubmissionSettings = SettingsField(
        title="Submission settings",
        default_factory=GafferDeadlineSubmissionSettings)


class GafferDeadlineSettings(BaseSettingsModel):
    node_type_submission_settings: list[GafferDeadlineSettingsNodetypeProfiles] = SettingsField(  # noqa
        title="Per Node type submission settings",
        description=("There needs to be a default value (with no node types), "
                     "that is the value that"
                     " will be used and visible in the publisher and supports "
                     "overriding by the user, the other values will _not_ be "
                     "available to the user to be overridden."),
        default_factory=list
    )
    env_vars: list[GafferDeadlineEnvVarModel] = SettingsField(
        title="Environment variables",
        default_factory=list
    )

    @validator('node_type_submission_settings')
    def assert_default_entry(cls, value):
        """Ensures that there is at least one entry with no node type
        specified.
        """

        for entry in value:
            if len(entry.node_type) == 0:
                break
        else:
            raise BadRequestException(f"There needs to be one entry with no "
                                      "node type specified")

        return value


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
        "node_type_submission_settings": [
            {
                "node_type": [],
                "submission_settings": {
                    "priority": 50,
                    "group": "",
                    "primary_pool": "",
                    "secondary_pool": "",
                },
            }
        ],
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
    }
}
