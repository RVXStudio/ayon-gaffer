import os

import Gaffer
import GafferImage
import GafferDispatch
import imath

from ayon_core.lib import Logger
from ayon_core.pipeline import registered_host
from ayon_core.pipeline.create import CreateContext
import pyblish

import ayon_gaffer

log = Logger.get_logger("ayon_gaffer.api.nodes.render_2d")

class Render2D(Gaffer.Box):
    def __init__(self, name="Render2D"):
        Gaffer.Box.__init__(self, name)

        self.addChild(Gaffer.StringPlug("localRender", defaultValue="localRender", flags=Gaffer.Plug.Flags.Default))
        self.addChild(Gaffer.StringPlug("farmRender", defaultValue="farmRender", flags=Gaffer.Plug.Flags.Default))
        self.addChild(
            Gaffer.StringPlug("readFromRender", defaultValue="readFromRender", flags=Gaffer.Plug.Flags.Default)
        )
        self.addChild(Gaffer.StringPlug("clearRender", defaultValue="clearRender", flags=Gaffer.Plug.Flags.Default))

        self.addChild(
            Gaffer.IntPlug("startFrame", Gaffer.Plug.Direction.In, defaultValue=0, flags=Gaffer.Plug.Flags.Default)
        )

        self.addChild(
            Gaffer.IntPlug("endFrame", Gaffer.Plug.Direction.In, defaultValue=100, flags=Gaffer.Plug.Flags.Default)
        )
        self.addChild(
            Gaffer.IntPlug("startHandle", Gaffer.Plug.Direction.In, defaultValue=0, flags=Gaffer.Plug.Flags.Default)
        )

        self.addChild(
            Gaffer.IntPlug("endHandle", Gaffer.Plug.Direction.In, defaultValue=0, flags=Gaffer.Plug.Flags.Default)
        )

        self.addChild(
            Gaffer.StringPlug("fileName", Gaffer.Plug.Direction.In, defaultValue="", flags=Gaffer.Plug.Flags.Default)
        )

    def submit_local_render(self):
        import GafferUI
        dispatcher = GafferDispatch.LocalDispatcher()

        dispatcher["framesMode"].setValue(2)  # custom range
        start_frame = self["startFrame"].getValue()
        end_frame = self["endFrame"].getValue()
        frange = f"{start_frame}-{end_frame}"
        dispatcher["frameRange"].setValue(frange)

        confirm = GafferUI.ConfirmationDialogue(title="Dispatch",
                                               message="Do you want to dispatch the job locally ?\n "
                                                       "this can take up some time.\n "
                                                       "You can track the job in the `Local Jobs` panel").waitForConfirmation()
        if confirm:
            dispatcher.dispatch([self["ImageWriter"]])
            GafferUI.ConfirmationDialogue(title="Job done", message="Job done").waitForConfirmation()

    def submit_farm_render(self):
        import GafferUI
        ayon_gaffer.api.set_root(self.scriptNode())
        host = registered_host()
        create_context = CreateContext(host)

        for instance in create_context.instances:
            if self.getName() != instance.transient_data["node"].getName():
                continue

            instance.data["active"] = True
            instance.data["publish"] = True
            instance.data["render_on_farm"] = True
            instance.data["creator_attributes"]["render_target"] = "farm"
            instance.data["node_name"] = self.getName()

        context = pyblish.api.Context()
        context.data["create_context"] = create_context
        
        # Since we need to bypass version validation and incrementing, we need to
        # remove the plugins from the list that are responsible for these tasks.
        plugins = pyblish.api.discover()
        blacklist = ["GafferIncrementCurrentFile", "ValidateVersion"]
        plugins = [
            plugin
            for plugin in plugins
            if plugin.__name__ not in blacklist
        ]

        context = pyblish.util.publish(context, plugins=plugins)

        error_message = ""
        success = True
        for result in context.data["results"]:
            if result["success"]:
                continue

            success = False

            err = result["error"]
            error_message += "\n"
            error_message += err.formatted_traceback

        if not success:
            GafferUI.ConfirmationDialogue(title="Error Rendering!", message=error_message).waitForButton()
            return

        GafferUI.ConfirmationDialogue(title="Submission Successful!", message="Submission to the farm was successful").waitForButton()


    def read_from_render(self):
        read_node = GafferImage.ImageReader("ReadFromRender")
        read_node["fileName"].setValue(self["fileName"])

    def clear_renders(self):
        dirpath = os.path.dirname(self["fileName"].getValue())
        for f in os.listdir(dirpath):
            path = os.path.join(dirpath, f)
            log.info("Removing: `{}`".format(path))
            os.remove(path)


Gaffer.Metadata.registerNode(
    Render2D,
    "description",
    "Renders 2D images",
    "nodeGadget:color",
    imath.Color3f(0.3203125, 0.125, 0.0),
    "noduleLayout:customGadget:addButtonTop:visible",
    False,
    "noduleLayout:customGadget:addButtonBottom:visible",
    False,
    "noduleLayout:customGadget:addButtonLeft:visible",
    False,
    "noduleLayout:customGadget:addButtonRight:visible",
    False,
    plugs={
        "localRender": [
            "nodule:type",
            "",
            "layout:section",
            "Settings",
            "plugValueWidget:type",
            "GafferUI.ButtonPlugValueWidget",
            "buttonPlugValueWidget:clicked",
            "plug.node().submit_local_render()",
            "label",
            "Render Local",
            "description",
            "Render Local (no publish)",
        ],
        "readFromRender": [
            "nodule:type",
            "",
            "layout:section",
            "Settings",
            "plugValueWidget:type",
            "GafferUI.ButtonPlugValueWidget",
            "buttonPlugValueWidget:clicked",
            "plug.node().read_from_render()",
            "label",
            "Read From Rendered",
            "description",
            "Create a Read node with the rendered images",
        ],
        "clearRender": [
            "nodule:type",
            "",
            "layout:section",
            "Settings",
            "plugValueWidget:type",
            "GafferUI.ButtonPlugValueWidget",
            "buttonPlugValueWidget:clicked",
            "plug.node().clear_renders()",
            "label",
            "Clear Renders",
            "description",
            "Delete all the rendered images on disk",
        ],
        "farmRender": [
            "nodule:type",
            "",
            "layout:section",
            "Settings",
            "plugValueWidget:type",
            "GafferUI.ButtonPlugValueWidget",
            "buttonPlugValueWidget:clicked",
            "plug.node().submit_farm_render()",
            "label",
            "Render on farm",
            "description",
            "Submit a farm job to render and a publish the images",
        ],
        "startFrame": [
            "nodule:type",
            "",
            "description",
            "The start frame for the render.",
            "layout:section",
            "Settings",
        ],
        "endFrame": [
            "nodule:type",
            "",
            "description",
            "The end frame for the render.",
            "layout:section",
            "Settings",
        ],
        "startHandle": [
            "nodule:type",
            "",
            "description",
            "The start frame handle for the render.",
            "layout:section",
            "Settings",
        ],
        "endHandle": [
            "nodule:type",
            "",
            "description",
            "The end frame handle for the render.",
            "layout:section",
            "Settings",
        ],
        "fileName": [
            "nodule:type",
            "",
            "description",
            "The output file name for the render.",
            "layout:section",
            "Settings",
        ],
    },
)
