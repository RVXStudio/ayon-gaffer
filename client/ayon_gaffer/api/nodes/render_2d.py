import Gaffer
import GafferImage
import GafferUI
import imath

class RenderNode2D(Gaffer.Box):
    def __init__(self, name="2DRender"):
        Gaffer.Box.__init__(self, name)

        # Add input plug for the image
        self.addChild(
            GafferImage.ImagePlug(
                "in", Gaffer.Plug.Direction.In,
                flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
            )
        )

        image_writer = GafferImage.ImageWriter("ImageWriter")
        self.addChild(image_writer)

        image_writer["in"].setInput(self["in"])
        self.addChild(Gaffer.StringPlug("localRender", defaultValue='',
                                                         flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ))
    def submit_local_render(self):
        print("toto")

Gaffer.Metadata.registerNode(
    RenderNode2D,
    "description", "I designate a render layer.",
    "nodeGadget:color", imath.Color3f(0.3203125, 0.125, 0.0),
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
