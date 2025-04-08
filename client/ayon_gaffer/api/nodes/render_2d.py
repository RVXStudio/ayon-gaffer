
import imath
import os

import GafferDispatch
import GafferImage
import GafferScene
import IECore
import Gaffer
from ayon_core.lib import Logger

log = Logger.get_logger("ayon_gaffer.api.nodes.render_layer")


class RenderNode2D(Gaffer.Box):
    def __init__(self, name="2DRender"):
        self.plug_signal = None

        Gaffer.Box.__init__(self, name)

        self.addChild(GafferImage.ImagePlug("in", Gaffer.Plug.Direction.In, flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic))

        image_writer = GafferImage.ImageWriter("ImageWriter")
        self.addChild(image_writer)

        image_writer["in"].setInput(self["in"])



Gaffer.Metadata.registerNode(
    RenderNode2D,
    "description",
    """
    I designate a render layer
    """,

    "nodeGadget:color", imath.Color3f(0.3203125, 0.125, 0),

    plugs={}
)
