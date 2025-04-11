import Gaffer
import GafferImage
import GafferDispatch
import GafferUI
import imath

class RenderNode2D(Gaffer.Box):
    def __init__(self, name="2DRender"):
        Gaffer.Box.__init__(self, name)

        self.addChild(
            GafferDispatch.TaskNode.TaskPlug(
                "preTask0", Gaffer.Plug.Direction.In,
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
            )
        )

        self.addChild(
            GafferImage.ImagePlug(
                "in", Gaffer.Plug.Direction.In,
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
            )
        )

        self.image_writer = GafferImage.ImageWriter("ImageWriter")
        self.addChild(self.image_writer)

        self.image_writer["in"].setInput(self["in"])

        self.image_writer['preTasks']['preTask0'].setInput(self["preTask0"])

        self.addChild(Gaffer.StringPlug("localRender", defaultValue='',
                                                         flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic))
        self.addChild(Gaffer.StringPlug("farmRender", defaultValue='',
                                        flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic))
        self.addChild(Gaffer.StringPlug("readFromRender", defaultValue='',
                                        flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic))
        self.addChild(Gaffer.StringPlug("clearRender", defaultValue='',
                                        flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic))

        self.addChild(
            Gaffer.IntPlug(
                "startFrame", Gaffer.Plug.Direction.In,
                defaultValue=0,
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
            )
        )

        self.addChild(
            Gaffer.IntPlug(
                "endFrame", Gaffer.Plug.Direction.In,
                defaultValue=100,
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
            )
        )

        self.addChild(
            Gaffer.StringPlug(
                "fileName", Gaffer.Plug.Direction.In,
                defaultValue="",
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
            )
        )
        self.image_writer["fileName"].setInput(self["fileName"])

    def submit_local_render(self):
        dispatcher = GafferDispatch.LocalDispatcher()

        dispatcher["framesMode"].setValue(2)  # custom range
        start_frame = self["startFrame"].getValue()
        end_frame = self["endFrame"].getValue()
        frange = f"{start_frame}-{end_frame}"
        dispatcher["frameRange"].setValue(frange)

        dispatcher.dispatch([self.image_writer])

    def submit_farm_render(self):
        raise NotImplementedError("Farm render is not implemented yet")

    def read_from_render(self):
        read_node = GafferImage.ImageReader("ReadFromRender")
        read_node["fileName"].setInput(self["fileName"])
        read_node.loadSequence()
        read_node["out"].setInput(self.image_writer["out"])

    def clear_renders(self):
        # todo how it is done in nuke ?
        raise NotImplementedError("Clear renders is not implemented yet")

Gaffer.Metadata.registerNode(
    RenderNode2D,
    # todo
    "description", "I designate a render layer.",
    "nodeGadget:color", imath.Color3f(0.3203125, 0.125, 0.0),
    'noduleLayout:customGadget:addButtonTop:visible', False,
    'noduleLayout:customGadget:addButtonBottom:visible', False,
    'noduleLayout:customGadget:addButtonLeft:visible', False,
    'noduleLayout:customGadget:addButtonRight:visible', False,
    plugs={
        "localRender": [
            "nodule:type", "",
            "layout:section", "Settings",
            "plugValueWidget:type", "GafferUI.ButtonPlugValueWidget",
            'buttonPlugValueWidget:clicked', 'plug.node().submit_local_render()',
            'label', 'Render Local',
        ],
        "readFromRender": [
            "nodule:type", "",
            "layout:section", "Settings",
            "plugValueWidget:type", "GafferUI.ButtonPlugValueWidget",
            'buttonPlugValueWidget:clicked', 'plug.node().read_from_render()',
            'label', 'Read From Rendered',
        ],
        "clearRender": [
            "nodule:type", "",
            "layout:section", "Settings",
            "plugValueWidget:type", "GafferUI.ButtonPlugValueWidget",
            'buttonPlugValueWidget:clicked', 'plug.node().clear_renders()',
            'label', 'Read From Rendered',
        ],
        "farmRender": [
            "nodule:type", "",
            "layout:section", "Settings",
            "plugValueWidget:type", "GafferUI.ButtonPlugValueWidget",
            'buttonPlugValueWidget:clicked', 'plug.node().submit_farm_render()',
            'label', 'Render Farm',
        ],
        "startFrame": [
            "nodule:type", "",
            "description", "The start frame for the render.",
            "layout:section", "Settings",
        ],
        "endFrame": [
            "nodule:type", "",
            "description", "The end frame for the render.",
            "layout:section", "Settings",
        ],
        "fileName": [
            "nodule:type", "",
            "description", "The output file name for the render.",
            "layout:section", "Settings",
        ],
    }
)

