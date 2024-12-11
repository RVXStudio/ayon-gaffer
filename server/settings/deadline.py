from pydantic import validator
from ayon_server.exceptions import BadRequestException
from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
)


from .common import PlugModel


class LimitGroupsSubmodel(BaseSettingsModel):
    _layout = "expanded"
    name: str = SettingsField(title="Limit name")
    value: list[str] = SettingsField(
        default_factory=list,
        title="Node type names that trigger limit"
    )


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


class GafferTaskNodeProfile(BaseSettingsModel):
    _layout = "expanded"
    type_names: list[str] = SettingsField(
        title="Task node Type names",
        default_factory=list,
    )
    plugs: list[PlugModel] = SettingsField(
        default_factory=list,
        title="Further filtering plugs",
    )


class GafferDeadlineSettingsNodetypeProfiles(BaseSettingsModel):
    _layout = "expanded"
    task_node: list[GafferTaskNodeProfile] = SettingsField(
        title="Task nodes",
        default_factory=list
    )
    submission_settings: GafferDeadlineSubmissionSettings = SettingsField(
        title="Submission settings",
        default_factory=GafferDeadlineSubmissionSettings)


class GafferDeadlineSettings(BaseSettingsModel):
    default_submission_settings: GafferDeadlineSubmissionSettings = SettingsField(  # noqa
        title="Default deadline submission settings",
        description=("The default submission settings. Used for the task "
                     "nodes that don't match anything in the per-node "
                     "settings")

    )
    task_node_submission_settings: list[GafferDeadlineSettingsNodetypeProfiles] = SettingsField(  # noqa
        title="Task node per-type submission settings",
        description=("If special submission settings are needed for certain "
                     "task nodes. Here is the place to set them."),
        default_factory=list
    )
    env_vars: list[GafferDeadlineEnvVarModel] = SettingsField(
        title="Environment variables",
        default_factory=list
    )
    limit_groups: list[LimitGroupsSubmodel] = SettingsField(
        default_factory=list,
        title="Limit Groups",
    )


DEFAULT_DEADLINE_SETTINGS = {
    "default_submission_settings": {
        "priority": 50,
        "group": "",
        "primary_pool": "",
        "secondary_pool": "",
    },
    "task_node_submission_settings": [
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
    "limit_groups": []
}
