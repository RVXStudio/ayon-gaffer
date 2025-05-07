from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
)
class CreateRender2dModel(BaseSettingsModel):
    temp_rendering_path_template: str = SettingsField(
        title="Temporary rendering path template"
    )

class CreatorPluginsSettings(BaseSettingsModel):
    CreateRender2d: CreateRender2dModel = SettingsField(
        default_factory=CreateRender2dModel,
        title="Create Render2D"
    )


DEFAULT_CREATE_SETTINGS = {
    "CreateRender2d": {
        "temp_rendering_path_template": "{work}/renders/gaffer/{product[name]}.{frame}.{ext}",
    }
}
