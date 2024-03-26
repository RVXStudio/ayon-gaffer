import imath
import Gaffer

from openpype.lib import Logger

log = Logger.get_logger('openpype.hosts.gaffer.api.nodes.render_settings')


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
        self.parentChangedSignal().connect(
            self.on_parent_changed, scoped=False)
        self.plugSetSignal().connect(self.on_plug_changed, scoped=False)

    def post_creation(self):
        self.add_resolution_multiplier_expression()

    def add_resolution_multiplier_expression(self):
        log.debug('adding resolution multiplier expression')
        expression_name = "update_resolution_multiplier"
        if expression_name in self.keys():
            log.debug("expression already there, skipping")
            return
        self.expression = Gaffer.Expression(expression_name)
        self.addChild(self.expression)
        self.expression["__in"].addChild(
            Gaffer.BoolPlug(
                "p0",
                defaultValue=False,
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
            ))
        self.expression["__in"].addChild(
            Gaffer.StringPlug(
                "p1",
                defaultValue='half',
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,))
        self.expression["__out"].addChild(
            Gaffer.FloatPlug(
                "p0",
                direction=Gaffer.Plug.Direction.Out,
                defaultValue=1.0,
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
                ))
        self.expression.addChild(
            Gaffer.V2fPlug(
                "__uiPosition",
                defaultValue=imath.V2f(0, 0),
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
                )
            )
        self.expression["__in"]["p0"].setInput(self["override_resolution"])
        self.expression["__in"]["p1"].setInput(
            self["override_resolution_mode"])
        self["resolution_multiplier"].setInput(self.expression["__out"]["p0"])
        self.expression["__uiPosition"].setValue(
            imath.V2f(8.90000057, 6.6500001))
        self.expression["__engine"].setValue('python')
        self.expression["__expression"].setValue(
            'if parent["__in"]["p0"]:\n'
            '    if parent["__in"]["p1"] == "half":\n'
            '        parent["__out"]["p0"] = 0.5\n'
            '    elif parent["__in"]["p1"] == "quarter":\n'
            '        parent["__out"]["p0"] = 0.25\n'
            '    else:\n'
            '        parent["__out"]["p0"] = 1.0\n'
            'else:\n'
            '    parent["__out"]["p0"] = 1.0\n'
        )

    def on_parent_changed(self, new_parent, old_parent):
        if new_parent is None:
            return
        self.reset_resolution()
        self.set_resolution()

    def on_plug_changed(self, plug):
        interesting_plugs = [
            "override_resolution",
            "override_resolution_mode",
            "custom_resolution"
        ]
        if plug.getName() in interesting_plugs:
            self.update()

    def update(self):
        if self["override_resolution"].getValue():
            # we are overriding the resolution; show the mode widget
            Gaffer.Metadata.registerValue(
               self["override_resolution_mode"],
               "plugValueWidget:type",
               "GafferUI.PresetsPlugValueWidget",
            )
            if self["override_resolution_mode"].getValue() == "custom":
                Gaffer.Metadata.registerValue(
                   self["custom_resolution"], "plugValueWidget:type", None)
                self["render_resolution"].setValue(
                    self["custom_resolution"].getValue())
            elif self["override_resolution_mode"].getValue() == "half":
                Gaffer.Metadata.registerValue(
                   self["custom_resolution"], "plugValueWidget:type", "")
                self.reset_resolution()
            elif self["override_resolution_mode"].getValue() == "quarter":
                Gaffer.Metadata.registerValue(
                   self["custom_resolution"], "plugValueWidget:type", "")
                self.reset_resolution()
        else:
            # hide the custom res plugs and reset
            Gaffer.Metadata.registerValue(
               self["override_resolution_mode"],
               "plugValueWidget:type",
               ""
            )
            Gaffer.Metadata.registerValue(
               self["custom_resolution"], "plugValueWidget:type", "")
            self.reset_resolution()
        self.set_resolution()

    def reset_resolution(self):
        if self.scriptNode() is None:
            return
        ctxt_res = self.scriptNode().context().get("ayon:resolution")
        if ctxt_res is None:
            log.error("Error getting resolution from context variables!")
            return
        self["render_resolution"].setValue(ctxt_res)

    def set_resolution(self):
        try:
            log.debug(
                f'setting resolution {self["render_resolution"].getValue()}')
            res_plug = self["StandardOptions"]["options"]["renderResolution"]
            res_plug["value"].setValue(self["render_resolution"].getValue())
        except Exception as err:
            log.error(f"Could not set resolution: {err}")


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
            "plugValueWidget:type", "",
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
            "readOnly", True,
            "layout:index", 4,
        ],

    }

)
