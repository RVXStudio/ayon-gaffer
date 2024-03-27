import os

import IECore
from ayon_gaffer.api.nodes import (
    AyonPublishTask,
    RenderLayerNode,
    RenderSettingsNode
)
import ayon_gaffer.api.pipeline
from ayon_gaffer import GAFFER_HOST_DIR


application = application  # noqa


IECore.registerRunTimeTyped(
    AyonPublishTask,
    typeName="AyonGaffer::AyonPublishTask"
)

IECore.registerRunTimeTyped(
    RenderLayerNode,
    typeName="AyonGaffer::RenderLayer"
)

IECore.registerRunTimeTyped(
    RenderSettingsNode,
    typeName="AyonGaffer::RenderSettings"
)


boxnode_path = os.path.join(GAFFER_HOST_DIR, "api", "nodes", "boxnodes")
ayon_gaffer.api.nodes.register_boxnode_path(boxnode_path)
ayon_gaffer.api.nodes.update_boxnode_menu(application)
