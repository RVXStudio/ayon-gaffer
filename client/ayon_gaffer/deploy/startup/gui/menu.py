# -*- coding: utf-8 -*-
"""AYON startup script.

Add AYON Menu entries to GafferUI
See: http://www.gafferhq.org/documentation/0.53.0.0/Tutorials/Scripting/AddingAMenuItem/index.html  # noqa

"""
from ayon_core.pipeline import install_host, registered_host
from ayon_gaffer.api import GafferHost, set_root, lib
from ayon_gaffer.api.pipeline import get_context_label
from ayon_core.lib import Logger

import GafferUI
import IECore

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
        {"command": lambda menu: set_frame_range_callback(menu)}
    )
    definition.append(
        f"Update context variables",
        {"command": lambda menu: update_root_context_variables_callback(menu)}
    )

    # Divider
    definition.append(f"WorkFilesDivider", {"divider": True})

    definition.append(
        f"Work Files...",
        {"command": lambda menu: host_tools.show_workfiles(
            parent=get_main_window(menu))}
    )
    return definition


def _install_ayon_menu():
    definition = GafferUI.ScriptWindow.menuDefinition(application)
    definition.append(menu_label, {"subMenu": ayon_menu})


def set_frame_range_callback(menu):
    scriptWindow = menu.ancestor(GafferUI.ScriptWindow)
    script_node = scriptWindow.scriptNode()
    lib.set_frame_range(script_node)


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


_install_ayon()
_install_ayon_menu()
