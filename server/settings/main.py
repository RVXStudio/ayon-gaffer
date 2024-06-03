from pydantic import Field
from ayon_server.settings import (
    BaseSettingsModel,
)


class GafferDeadlineEnvVarModel(BaseSettingsModel):
    _layout = "expanded"
    name: str = Field(
        title="Variable name"
    )
    use_env_value: bool = Field(
        title="Copy value from environment"
    )
    value: str = Field(
        title="Variable value"
    )


class GafferDeadlinePoolSettings(BaseSettingsModel):
    primary_pool: str = Field(
        title="Primary Pool"
    )
    secondary_pool: str = Field(
        title="Secondary Pool"
    )
    group: str = Field(
        title="Group"
    )


class GafferDeadlineSettings(BaseSettingsModel):
    env_vars: list[GafferDeadlineEnvVarModel] = Field(
        title="Environment variables",
        default_factory=list
    )
    pools: GafferDeadlinePoolSettings = Field(
        default_factory=GafferDeadlinePoolSettings,
        title="Pools"
    )


class GafferSettings(BaseSettingsModel):
    node_preset_paths: list[str] = Field(
        default_factory=list,
        title="Node preset paths"
    )
    deadline: GafferDeadlineSettings = Field(
        default_factory=GafferDeadlineSettings,
        title="GafferDeadline"
    )


DEFAULT_VALUES = {
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
