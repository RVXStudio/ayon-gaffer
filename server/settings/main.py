from pydantic import Field
from ayon_server.settings import (
    BaseSettingsModel,
    TemplateWorkfileBaseOptions,
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


class GafferDeadlineExtraSettings(BaseSettingsModel):
    group: str = Field(
        title="Group"
    )


class GafferDeadlineSettings(BaseSettingsModel):
    env_vars: list[GafferDeadlineEnvVarModel] = Field(
        title="Environment variables",
        default_factory=list
    )
    extra: GafferDeadlineExtraSettings = Field(
        default_factory=GafferDeadlineExtraSettings,
        title="Extra"
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
            {"name": "GAFFER_EXTENSION_PATHS", "use_env_value": True, "value": ""},
            {"name": "AVALON_APP_NAME", "use_env_value": True, "value": ""},
            {"name": "AVALON_TASK", "use_env_value": True, "value": ""},
            {"name": "AVALON_PROJECT", "use_env_value": True, "value": ""},
            {"name": "AVALON_ASSET", "use_env_value": True, "value": ""},
            {"name": "AYON_BUNDLE_NAME", "use_env_value": True, "value": ""},
            {"name": "AYON_RENDER_JOB", "use_env_value": False, "value": "1"},
        ],
        "extra": {
            "group": "skjoldur"
        }
    }
}
