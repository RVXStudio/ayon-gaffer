import imath
import os

import GafferDispatch
import GafferImage
import GafferScene
import IECore
import Gaffer
from ayon_core.lib import Logger

DEFAULT_OUTPUT_PATH = "${project:rootDirectory}/${script:name}/{layer_name}"

log = Logger.get_logger("ayon_gaffer.api.nodes.render_layer")


class RenderLayerNode(Gaffer.Box):
    def __init__(self, name="RenderLayer"):
        self.plug_signal = None

        Gaffer.Box.__init__(self, name)

        self.addChild(Gaffer.StringPlug(
            "layer_name",
            flags=Gaffer.Plug.Flags.Default
        ))

        self.addChild(Gaffer.StringPlug(
            "frame_range",
            flags=Gaffer.Plug.Flags.Default,
            defaultValue="timeline"
        ))

        self.addChild(Gaffer.StringPlug(
            "layer_output_path",
            flags=Gaffer.Plug.Flags.Default,
            defaultValue=DEFAULT_OUTPUT_PATH)
        )

        self.addChild(Gaffer.BoolPlug(
            "merge_aovs",
            flags=Gaffer.Plug.Flags.Default,
            defaultValue=True
        ))

        outputs_plug = Gaffer.CompoundDataPlug(
            "outputs",
            flags=Gaffer.Plug.Flags.Default
        )
        self.addChild(outputs_plug)

        layer_range_plug = Gaffer.V2iPlug(
            "layer_range",
            defaultValue=imath.V2i(0, 0),
            flags=Gaffer.Plug.Flags.Default
        )
        self.addChild(layer_range_plug)

        node_name_plug = Gaffer.StringPlug(
            "node_name",
            defaultValue=self.getName(),
            flags=Gaffer.Plug.Flags.Default
        )
        self.addChild(node_name_plug)

    def connect_signals(self):
        if self.plug_signal is None:
            log.debug("Connecting plugSetSignal")
            self.plug_signal = self.plugSetSignal()
            self.plug_signal.connect(self.on_plug_changed, scoped=False)
        # self.parentChangedSignal().connect(self.notify_parent, scoped=False)
        self.nameChangedSignal().connect(self.name_changed, scoped=False)
        self.name_changed()

    def name_changed(self, *args):
        self["node_name"].setValue(self.getName())

    def on_plug_changed(self, plug):
        if plug.getName() == "layer_name":
            Gaffer.Metadata.registerValue(
                self,
                'annotation:user:text',
                plug.getValue()
            )


Gaffer.Metadata.registerNode(
    RenderLayerNode,
    "description",
    """
    I designate a render layer
    """,

    "nodeGadget:color", imath.Color3f(0.3203125, 0.125, 0),

    plugs={

        "node_name": [
            "description",
            '''
            The output path of the render layer. Takes some tags and some fancy
            stuff.
            ''',
            "nodule:type", "",
            "plugValueWidget:type", "",
        ],

        "outputs": [
            "description",
            """
            The outputs this render layer creates this is a list of strings
            where the entries are in the form:
              <aov_name>::<path_to_output_files>
            """,
            "label", "Outputs",
            "layout:section", "Outputs",
            "nodule:type", ""
        ],

        'layer_name': [
            "description",
            '''
            Name of the render layer
            ''',
            "label", "Layer name",
            "layout:section", "Render Layer",
            "nodule:type", ""
        ],

        "layer_output_path": [
            "description",
            '''
            The output path of the render layer. Takes some tags and some fancy
            stuff.
            ''',
            "label", "Layer output path",
            "layout:section", "Outputs",
            "nodule:type", "",
        ],

        "merge_aovs": [
            "description",
            '''
            Should we merge the aovs
            ''',
            "label", "Merge AOVs",
            "layout:section", "Outputs",
            "nodule:type", "",
            "readOnly", True,
            "divider", True,
        ],

        "frame_range": [
            "description",
            """
            Specify frame range
            """,
            "nodule:type", "",
            "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
            "preset:layer_range", "layer_range",
            "preset:timeline", "timeline",
            "preset:first_last", "first_last",
            "preset:full_range", "full_range",
            "preset:start_end", "start_end",
            "preset:custom", "custom",
            "layout:section", "Render Layer",
        ],
        "layer_range": [
            "description",
            """
            A field to have the full shot range - to be loaded by spreadsheet
            """,
            "nodule:type", "",
            "layout:section", "Render Layer",
            "layout:index", 5,
        ],

        "out_render": [
            "description",
            """
            Render task plug.
            """,
            "plugValueWidget:type", "",
        ],

    }

)
