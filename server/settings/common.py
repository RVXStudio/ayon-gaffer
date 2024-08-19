from ayon_server.settings import BaseSettingsModel, SettingsField


class V2fPlug(BaseSettingsModel):
    _layout = "compact"

    x: float = SettingsField(1.0, title="X")
    y: float = SettingsField(1.0, title="Y")


class V3fPlug(BaseSettingsModel):
    _layout = "compact"

    x: float = SettingsField(1.0, title="X")
    y: float = SettingsField(1.0, title="Y")
    z: float = SettingsField(1.0, title="Z")


class Color3fPlug(BaseSettingsModel):
    _layout = "compact"

    r: float = SettingsField(1.0, title="R")
    g: float = SettingsField(1.0, title="G")
    b: float = SettingsField(1.0, title="B")


class Color4fPlug(BaseSettingsModel):
    _layout = "compact"

    r: float = SettingsField(1.0, title="R")
    g: float = SettingsField(1.0, title="G")
    b: float = SettingsField(1.0, title="B")
    a: float = SettingsField(1.0, title="A")


plug_types_enum = [
    {"value": "text", "label": "String"},
    {"value": "boolean", "label": "Boolean"},
    {"value": "number", "label": "Integer"},
    {"value": "decimal", "label": "Float"},
    {"value": "v2f", "label": "2D vector"},
    {"value": "v3f", "label": "3D vector"},
    {"value": "color3f", "label": "Color3f"},
    {"value": "color4f", "label": "Color4f"},
]


class PlugModel(BaseSettingsModel):
    _layout = "expanded"

    type: str = SettingsField(
        title="Type",
        description="Switch between different plug types",
        enum_resolver=lambda: plug_types_enum,
        conditionalEnum=True
    )

    name: str = SettingsField(
        title="Name",
        placeholder="Name"
    )
    text: str = SettingsField("", title="Value")
    boolean: bool = SettingsField(False, title="Value")
    number: int = SettingsField(0, title="Value")
    decimal: float = SettingsField(0.0, title="Value")
    v2f: V2fPlug = SettingsField(
        default_factory=V2fPlug,
        title="Value"
    )
    v3f: V3fPlug = SettingsField(
        default_factory=V3fPlug,
        title="Value"
    )
    color3f: Color3fPlug = SettingsField(
        default_factory=Color3fPlug,
        title="RGBA Float"
    )
    color4f: Color4fPlug = SettingsField(
        default_factory=Color4fPlug,
        title="RGBA Float"
    )