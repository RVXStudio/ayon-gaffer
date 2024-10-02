from pydantic import validator
from ayon_server.exceptions import BadRequestException
from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
    ensure_unique_names
)
import re

from .common import PlugModel


class LoaderTemplateProfileModel(BaseSettingsModel):
    _layout = "expanded"
    product_type: list[str] = SettingsField(
        title="Imported product type",
        default_factory=list
    )
    task_name: list[str] = SettingsField(
        title="Current task",
        default_factory=list
    )
    node_name_template: str = SettingsField(
        default="",
        title="Node name template"
    )
    scenegraph_location_template: str = SettingsField(
        default="",
        title="Scenegraph location template"
    )
    auxiliary_transforms: list[str] = SettingsField(
        default_factory=list,
        title="Auxiliary transforms"
    )

    @validator('node_name_template')
    def only_one_hash_block(cls, value):
        """Ensures only one list is used."""

        res = re.findall(r'(#+)', value)
        if res is not None and len(res) > 1:
            raise BadRequestException(f"Only one set of # can be used.")

        return value


class LoadSceneModel(BaseSettingsModel):
    enabled: bool = SettingsField(
        title="Enabled"
    )

    template_profiles: list[LoaderTemplateProfileModel] = SettingsField(
        title="SceneReader node name profiles",
        default_factory=list
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
        "template_profiles": [
            {
                "product_type": ["model"],
                "task_name": [],
                "node_name_template": "{folder[fullname]}_{ext}",
                "scenegraph_location_template": "{node}/geo",
                "auxiliary_transforms": ["mat"]
            }
        ]
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
