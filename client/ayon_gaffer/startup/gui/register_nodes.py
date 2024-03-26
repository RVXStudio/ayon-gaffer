import os

import IECore
from openpype.hosts.gaffer.api.nodes import (
    AyonPublishTask,
    RenderLayerNode,
    RenderSettingsNode
)
import openpype.hosts.gaffer.api.pipeline
from openpype.hosts.gaffer import GAFFER_HOST_DIR


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
openpype.hosts.gaffer.api.nodes.register_boxnode_path(boxnode_path)
openpype.hosts.gaffer.api.nodes.update_boxnode_menu(application)
