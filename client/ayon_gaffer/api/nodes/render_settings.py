import imath
import Gaffer

from ayon_core.lib import Logger

log = Logger.get_logger('ayon_gaffer.api.nodes.render_settings')


class RenderSettingsNode(Gaffer.Box):
    def __init__(self, name="RenderSettings"):
        Gaffer.Box.__init__(self, name)

        self.addChild(
            Gaffer.V2iPlug(
                "render_resolution",
                defaultValue=imath.V2i(3840, 2160),
                flags=Gaffer.Plug.Flags.Default
            )
        )
        self.addChild(
            Gaffer.BoolPlug(
                "override_resolution",
                defaultValue=False,
                flags=Gaffer.Plug.Flags.Default
            )
        )

        self.addChild(
            Gaffer.BoolPlug(
                "use_custom_resolution",
                defaultValue=False,
                flags=Gaffer.Plug.Flags.Default
            )
        )

        self.addChild(
            Gaffer.StringPlug(
                "override_resolution_mode",
                defaultValue="half",
                flags=Gaffer.Plug.Flags.Default
            )
        )
        self.addChild(
            Gaffer.V2iPlug(
                "custom_resolution",
                defaultValue=imath.V2i(3840, 2160),
                flags=Gaffer.Plug.Flags.Default
            )
        )
        self.addChild(
            Gaffer.FloatPlug(
                "resolution_multiplier",
                defaultValue=1.0,
                flags=Gaffer.Plug.Flags.Default
            )
        )
        self.addChild(
            Gaffer.V2iPlug(
                "effective_resolution",
                defaultValue=imath.V2i(3840, 2160),
                flags=Gaffer.Plug.Flags.Default
            )
        )


Gaffer.Metadata.registerNode(
    RenderSettingsNode,
    "description",
    """
    I designate render settings
    """,

    "nodeGadget:color", imath.Color3f(0.3203125, 0.125, 0),

    plugs={
        'render_resolution': [
            "description",
            '''
            Render resolution
            ''',
            "label", "Render resolution",
            "layout:section", "Common.Image Size",
            "layout:index", 0,
            "nodule:type", "",
            "readOnly", True
        ],
        'override_resolution': [
            "description",
            '''
            Override the Ayon supplied resolution
            ''',
            "label", "Override resolution",
            "layout:section", "Common.Image Size",
            "layout:index", 1,
            "nodule:type", "",
            "plugValueWidget", "",
        ],
        'use_custom_resolution': [
            "description",
            '''
            Use custom version
            ''',
            "label", "Use custom version",
            "layout:section", "Common.Image Size",
            "layout:index", 1,
            "nodule:type", "",
            "plugValueWidget", "",
        ],
        'override_resolution_mode': [
            "description",
            '''
            How should we override the resolution
            ''',
            "label", "New resolution",
            "layout:section", "Common.Image Size",
            "nodule:type", "",
            "preset:Half res", "half",
            "preset:Quarter res", "quarter",
            "preset:Custom", "custom",
            "plugValueWidget:type", "",
            "layout:index", 2,
        ],
        'custom_resolution': [
            "description",
            '''
            Custom render resolution
            ''',
            "label", "Custom resolution",
            "layout:section", "Common.Image Size",
            "nodule:type", "",
            "layout:index", 3,
        ],
        'resolution_multiplier': [
            "description",
            '''
            Multiplier on the resolution
            ''',
            "label", "Resolution multiplier",
            "layout:section", "Common.Image Size",
            "nodule:type", "",
            "layout:index", 4,
        ],
        'effective_resolution': [
            "description",
            '''
            The used resolution
            ''',
            "label", "Effective resolution",
            "layout:section", "Common.Image Size",
            "nodule:type", "",
            "layout:index", 5,
            "readOnly", True
        ],

    }

)
