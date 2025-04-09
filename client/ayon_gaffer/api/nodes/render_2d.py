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
                                                         flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ))
    def submit_local_render(self):
        print("toto")
        dispatcher = GafferDispatch.LocalDispatcher()
        dispatcher["framesMode"].setValue(2)  # custom range
        frange = f"1001-1003"
        dispatcher["frameRange"].setValue(frange)

        filename = "/net-home/pierrer/Desktop/test_render_####.exr"
        self.image_writer["fileName"].setValue(filename)
        dispatcher.dispatch([self.image_writer])


Gaffer.Metadata.registerNode(
    RenderNode2D,
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
            'label', 'Submit Render Local',
        ]
    }
)
