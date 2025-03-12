from pydantic import validator
from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
    ensure_unique_names,
)


class ImageIOFileRuleModel(BaseSettingsModel):
    name: str = SettingsField("", title="Rule name")
    pattern: str = SettingsField("", title="Regex pattern")
    colorspace: str = SettingsField("", title="Colorspace name")
    ext: str = SettingsField("", title="File extension")


class ImageIOFileRulesModel(BaseSettingsModel):
    _isGroup: bool = True

    activate_host_rules: bool = SettingsField(False)
    rules: list[ImageIOFileRuleModel] = SettingsField(
        default_factory=list,
        title="Rules"
    )

    @validator("rules")
    def validate_unique_outputs(cls, value):
        ensure_unique_names(value)
        return value


class ImageIOSettings(BaseSettingsModel):
    """Gaffer color management settings."""

    activate_host_color_management: bool = SettingsField(
        True, title="Enable Color Management")
    file_rules: ImageIOFileRulesModel = SettingsField(
        default_factory=ImageIOFileRulesModel,
        title="File Rules"
    )
    working_color_space: str = SettingsField(default_factory=str, title="Working Color Space")
    colorspace_display_transform: str = SettingsField(default_factory=str, title="Color Space Display Transform")

DEFAULT_IMAGEIO_SETTINGS = {
    "activate_host_color_management": True,
    "working_color_space": "ACEScg",
    "colorspace_display_transform": "sRGB - Display/ACES 1.0 - SDR Video",
    "file_rules": {
        "activate_host_rules": False,
        "rules": []
    }
}
