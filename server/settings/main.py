from pydantic import Field, validator
import json
from ayon_server.exceptions import BadRequestException
from ayon_server.settings import (
    BaseSettingsModel,
    TemplateWorkfileBaseOptions,
)


def validate_json_dict(value):
    if not value.strip():
        return "{}"
    try:
        converted_value = json.loads(value)
        success = isinstance(converted_value, dict)
    except json.JSONDecodeError:
        success = False

    if not success:
        raise BadRequestException(
            "Environment's can't be parsed as json object"
        )
    return value


class TestModel(BaseSettingsModel):
    enabled: bool = Field(True)
    optional: bool = Field(title="Optional")
    active: bool = Field(title="Active")
    presets: str = Field("", title="Presets", widget="textarea")

    @validator("presets")
    def validate_json(cls, value):
        return validate_json_dict(value)


class GafferSettings(BaseSettingsModel):
    tester: TestModel = Field(
        default_factory=TestModel,
        title="Test settings")


DEFAULT_VALUES = {
    "tester": {
        "enabled": True,
        "optional": False,
        "active": True,
        "presets": '{"FANTASTIC": "YES"}'
    },
}
