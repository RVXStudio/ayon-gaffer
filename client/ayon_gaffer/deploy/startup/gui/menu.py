# -*- coding: utf-8 -*-
"""AYON startup script.

Add AYON Menu entries to GafferUI
See: http://www.gafferhq.org/documentation/0.53.0.0/Tutorials/Scripting/AddingAMenuItem/index.html  # noqa

"""
from ayon_core.pipeline import install_host, registered_host
from ayon_core.tools.workfile_template_build import open_template_ui
from ayon_gaffer.api import GafferHost, set_root, lib
from ayon_gaffer.api.pipeline import get_context_label, update_annotations, update_annotations_on_all_nodes
from ayon_core.lib import Logger
import ayon_gaffer.api.nodes.lib
from ayon_gaffer.api.workfile_template_builder import (
    build_workfile_template,
    create_placeholder,
    update_placeholder,
    GafferTemplateBuilder,
)
import ayon_gaffer.api.pipeline
from ayon_gaffer.api.nodes import (
    RenderLayerNode,
)
import GafferUI
import Gaffer
import IECore
import functools

log = Logger.get_logger("ayon_gaffer.startup.gui.menu")

# Make sure linter ignores undefined `application`, Gaffer startup provides it
application = application # noqa

menu_label = 'AYON'


def ayon_menu(menu):
    from ayon_core.tools.utils import host_tools

    def get_main_window(menu):
        script_window = menu.ancestor(GafferUI.ScriptWindow)
        set_root(script_window.scriptNode())     # todo: avoid hack
        return script_window._qtWidget()

    def get_script_node(menu):
        return menu.ancestor(GafferUI.ScriptWindow).scriptNode()

    definition = IECore.MenuDefinition()
    context_label = get_context_label().replace('/', '|')
    definition.append(context_label, {"command": None, "active": False})
    definition.append("contextDivider", {"divider": True})

    definition.append(
        f"Create...",
        {"command": lambda menu: host_tools.show_publisher(
            parent=get_main_window(menu),
            tab="create")}
    )
    definition.append(
        f"Load...",
        {"command": lambda menu: host_tools.show_loader(
            parent=get_main_window(menu),
            use_context=True)}
    )
    definition.append(
        f"Publish...",
        {"command": lambda menu: host_tools.show_publisher(
            parent=get_main_window(menu),
            tab="publish")}
    )
    definition.append(
        f"Manage...",
        {"command": lambda menu: host_tools.show_scene_inventory(
            parent=get_main_window(menu))}
    )
    definition.append(
        f"Library...",
        {"command": lambda menu: host_tools.show_library_loader(
            parent=get_main_window(menu))}
    )

    # Divider
    definition.append(f"ActionsDivider", {"divider": True})
    definition.append(
        f"Set frame range...",
        {
            "command": lambda menu: set_frame_range_callback(menu),
            "description": "Set the script time slider to the context range"
        }
    )
    definition.append(
        f"Update context variables",
        {"command": lambda menu: update_root_context_variables_callback(menu)}
    )

    definition.append(
        "/Update renderlayer range/Selected nodes",
        {
            "command": lambda menu: update_range_for_selected_layers(menu),
            "description": "Update the frame range for the selected layers"
        }
    )
    definition.append(
        "/Update renderlayer range/All nodes",
        {
            "command": lambda menu: update_range_for_all_layers(menu),
            "description": "Update the frame range for all layers"
        }
    )
    definition.append(
        "/Update selected containers",
        {
            "command": lambda menu: update_selcted_containers(menu),
            "description": "Update the selected containers to the latest version"
        }
    )

    # Divider
    definition.append(f"WorkFilesDivider", {"divider": True})

    definition.append(
        f"Work Files...",
        {"command": lambda menu: host_tools.show_workfiles(
            parent=get_main_window(menu))}
    )
    # Divider
    definition.append(f"TemplatesDivider", {"divider": True})

    definition.append(f"/Template Builder/Build Workfile from Template", {"command": lambda: build_workfile_template(parent=get_main_window(menu))})

    definition.append(
        "/Template Builder/Open template",
        {"command": lambda menu: open_template_ui(GafferTemplateBuilder(registered_host()), get_main_window(menu))},
    )
    definition.append(
        "/Template Builder/Create Place Holder", {"command": lambda menu: create_placeholder(get_main_window(menu))}
    )
    definition.append(
        "/Template Builder/Update Place Holder", {"command": lambda menu: update_placeholder(get_script_node(menu), get_main_window(menu))}
    )

    return definition


def _install_boxnode_context_menu():
    """
    Add the Save boxnode context menu. It will only be added to Box nodes,
    not subclasses (since they have maybe some custom logic in their node
    definitions e.g. api/nodes/render_layer.py)

    """
    def __boxnode_context_menu(graphEditor, node, menuDefinition):

        if node.typeName() != "Gaffer::Box":
            return

        menuDefinition.append(
            "/boxnodedivider",
            {
                "divider": True
            }
        )

        menuDefinition.append(
            "/Save boxnode",
            {
                "command": functools.partial(
                    ayon_gaffer.api.nodes.lib.export_selected_node_as_boxnode,
                    node,
                    graphEditor)
            }
        )

    GafferUI.GraphEditor.nodeContextMenuSignal().connect(
        __boxnode_context_menu, scoped=False)


def _install_ayon_menu():
    definition = GafferUI.ScriptWindow.menuDefinition(application)
    definition.append(menu_label, {"subMenu": ayon_menu})


def set_frame_range_callback(menu):
    scriptWindow = menu.ancestor(GafferUI.ScriptWindow)
    script_node = scriptWindow.scriptNode()
    lib.set_frame_range(script_node)


def update_range_for_selected_layers(menu):
    scriptWindow = menu.ancestor(GafferUI.ScriptWindow)
    script_node = scriptWindow.scriptNode()
    selection = script_node.selection()
    # find RenderLayerNodes in the selection
    nodes = [node for node in selection if isinstance(node, RenderLayerNode)]
    ayon_gaffer.api.pipeline.update_range_on_layers(nodes)


def update_range_for_all_layers(menu):
    scriptWindow = menu.ancestor(GafferUI.ScriptWindow)
    script_node = scriptWindow.scriptNode()
    ayon_gaffer.api.pipeline.update_range_on_layers(
        script_node.children(RenderLayerNode)
    )

def update_selcted_containers(menu):
    script_window = menu.ancestor(GafferUI.ScriptWindow)
    set_root(script_window.scriptNode())
    ayon_gaffer.api.pipeline.update_selected_container(script_window)


def update_root_context_variables_callback(menu):
    host = registered_host()

    scriptWindow = menu.ancestor(GafferUI.ScriptWindow)
    script_node = scriptWindow.scriptNode()
    ayon_context = host.get_current_context()
    lib.update_root_context_variables(
        script_node,
        ayon_context["project_name"],
        ayon_context["folder_path"]
    )


def _install_ayon():
    log.info("Installing ayon ...")
    install_host(GafferHost(application))


def _on_set_plug(plug):
    if plug.getName() == "representation":
        update_annotations(plug.parent().parent())


def _on_new_user_plug(_, plug):
    if plug.getName() == "representation":
        update_annotations(plug.parent().parent())


def _is_node_to_annotate(node):
    return "user" in node and "id" in node["user"] and node["user"]["id"].getValue() == "ayon.load.container"


def _on_new_node(_, node):
    if _is_node_to_annotate(node):
        node["user"].childAddedSignal().connect(_on_new_user_plug, scoped=False)
        node.plugSetSignal().connect(_on_set_plug, scoped=False)


def _on_scene_new(_, script_node):
    set_root(script_node)
    script_node.childAddedSignal().connect(_on_new_node, scoped=False)
    for node in script_node.children():
        if _is_node_to_annotate(node):
            node.plugSetSignal().connect(_on_set_plug, scoped=False)

    update_annotations_on_all_nodes()


_install_ayon()
_install_ayon_menu()

_install_boxnode_context_menu()

scripts_list = application.root()["scripts"]  # noqa
scripts_list.childAddedSignal().connect(_on_scene_new, scoped=False)
