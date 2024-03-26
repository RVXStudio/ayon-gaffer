# -*- coding: utf-8 -*-
"""OpenPype startup script.

Add OpenPype Menu entries to GafferUI
See: http://www.gafferhq.org/documentation/0.53.0.0/Tutorials/Scripting/AddingAMenuItem/index.html  # noqa

"""
from openpype.pipeline import install_host, registered_host
from openpype.hosts.gaffer.api import GafferHost, set_root, lib
from openpype.hosts.gaffer.api.pipeline import get_context_label
from openpype import AYON_SERVER_ENABLED
from openpype.lib import Logger

import GafferUI
import IECore

log = Logger.get_logger("openpype.hosts.gaffer.startup.gui.menu")

# Make sure linter ignores undefined `application`, Gaffer startup provides it
application = application # noqa

if AYON_SERVER_ENABLED:
    menu_label = 'AYON'
else:
    menu_label = 'OpenPype'


def ayon_menu(menu):
    from openpype.tools.utils import host_tools

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


def _install_openpype_menu():
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
        ayon_context["asset_name"]
    )


def _install_openpype():
    log.info("Installing OpenPype ...")
    install_host(GafferHost(application))


_install_openpype()
_install_openpype_menu()
