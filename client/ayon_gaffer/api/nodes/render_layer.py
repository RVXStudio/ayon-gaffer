import imath
import os

import GafferDispatch
import GafferImage
import GafferScene
import IECore
import Gaffer
from openpype.lib import Logger

DEFAULT_OUTPUT_PATH = "${project:rootDirectory}/${script:name}/{layer_name}"

log = Logger.get_logger("ayon_gaffer.api.nodes.render_layer")


def sync_plugs_to_contexts(node):
    context_nodes = node.children(Gaffer.ContextVariables)
    plugs = node.children(Gaffer.Plug)
    plug_names = {p.getName(): p for p in plugs}
    log.debug("Syncing plugs to context")
    for ctxt in context_nodes:
        for ctx_var in ctxt["variables"]:
            var_name = ctx_var["name"].getValue()
            if var_name in plug_names.keys():
                ctx_var["value"].setValue(plug_names[var_name].getValue())


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
            defaultValue="layer_range"
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

        cleanup_paths_plug = Gaffer.StringVectorDataPlug(
            "cleanup_paths",
            defaultValue=IECore.StringVectorData([]),
            flags=Gaffer.Plug.Flags.Default
        )
        self.addChild(cleanup_paths_plug)

        layer_range_plug = Gaffer.V2iPlug(
            "layer_range",
            defaultValue=imath.V2i(0, 0),
            flags=Gaffer.Plug.Flags.Default
        )
        self.addChild(layer_range_plug)

    def connect_signals(self):
        if self.plug_signal is None:
            log.debug("Connecting plugSetSignal")
            self.plug_signal = self.plugSetSignal()
            self.plug_signal.connect(self.on_plug_changed, scoped=False)
        # self.parentChangedSignal().connect(self.notify_parent, scoped=False)
        # self.childAddedSignal().connect(self.notify_name, scoped=False)

    def on_plug_changed(self, plug):
        if plug.getName() == 'outputs':
            return

        if plug.getName() == "layer_name":
            Gaffer.Metadata.registerValue(
                self,
                'annotation:user:text',
                plug.getValue()
            )

        output_affecting_plug_names = [
            "layer_name",
            "layer_type",
            "layer_output_path",
            "merge_aovs"
        ]

        if (plug.getName() in output_affecting_plug_names or
                'aovExp' in plug.getName()):
            # first get the render outputs
            sync_plugs_to_contexts(self)
            self.update_outputs()

    def update_outputs(self):
        res = {}
        if self.scriptNode() is None:
            log.warning("Script node is None, aborting")
            return
        with Gaffer.Context(self.scriptNode().context()) as context:
            context['layer_output_path'] = self['layer_output_path'].getValue()
            context['layer_name'] = self['layer_name'].getValue()
            context['layer_type'] = self['layer_type'].getValue()
            if not self["merge_aovs"].getValue():
                val = self["arnold_render"]["out"].globals()
                for k in val.keys():
                    if k.startswith('output:Batch'):
                        res[k.split('/')[-1]] = val[k].getName()

            imagewriters = self.children(GafferImage.ImageWriter)
            for iw in imagewriters:
                iw_name = iw.getName()
                iw_outplug = iw['task']
                switch_plugs = [o for o in iw_outplug.outputs()
                                if o.node().typeName() == 'Gaffer::Switch']
                if len(switch_plugs) == 1:
                    plug_number = int(
                        switch_plugs[0].getName().replace('in', ''))
                    index_val = switch_plugs[0].node()['index'].getValue()
                    if plug_number != index_val:
                        log.debug(f"Skipping {switch_plugs[0].fullName()}"
                                  "since it's being bypassed by a switch")
                        continue

                output_name = iw_name.replace('ImageWriter', '')
                # output_path = context.substitute(iw['fileName'].getValue())
                output_path = iw['fileName'].getValue()
                res[output_name] = output_path

            self["outputs"].clearChildren()
            for output, path in res.items():
                try:
                    new_outplug = Gaffer.NameValuePlug(
                        output,
                        Gaffer.StringPlug(
                            f"value_{output}",
                            defaultValue='',
                            flags=(Gaffer.Plug.Flags.Default |
                                   Gaffer.Plug.Flags.Dynamic)
                        ),
                        True,
                        f"aov_{output}",
                        Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
                    )
                except Exception as err:
                    log.error('Error creating plugs for outputs', err)
                new_outplug["value"].setValue(path)
                self["outputs"].addChild(new_outplug)


Gaffer.Metadata.registerNode(
    RenderLayerNode,
    "description",
    """
    I designate a render layer
    """,

    "nodeGadget:color", imath.Color3f(0.3203125, 0.125, 0),

    plugs={
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

        "cleanup_paths": [
            "description",
            """
            A list of paths that should be cleaned up after publishing
            """,
            "label", "Cleanup Paths",
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
