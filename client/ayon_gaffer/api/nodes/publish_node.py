import imath

import GafferDispatch
import IECore
import Gaffer


class AyonPublishTask(GafferDispatch.TaskNode):
    def __init__(self, name="AYON_task"):

        GafferDispatch.TaskNode.__init__(self, name)

    def hash(self, context):

        h = GafferDispatch.TaskNode.hash(self, context)
        h.append(IECore.MurmurHash())

        return h


Gaffer.Metadata.registerNode(
    AyonPublishTask,
    "description",
    """
    I designate a publish context. Feed me RenderLayers!
    """,

    "nodeGadget:color", imath.Color3f(0.3203125, 0.125, 0),
    "defaulticon", "AYON_icon_dev.png",
    "icon", "AYON_icon_dev.png",
)
