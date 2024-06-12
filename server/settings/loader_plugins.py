from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
)


class LoadSceneModel(BaseSettingsModel):
    enabled: bool = SettingsField(
        title="Enabled"
    )

    node_name_template: str = SettingsField(
        title="SceneReader node name template"
    )


class LoaderPluginsModel(BaseSettingsModel):
    GafferLoadScene: LoadSceneModel = SettingsField(
        default_factory=LoadSceneModel,
        title="Load Scene"
    )


DEFAULT_LOADER_PLUGINS_SETTINGS = {
    "GafferLoadScene": {
        "enabled": True,
        "node_name_template": "{folder[fullname]}_{ext}"
    }
}
