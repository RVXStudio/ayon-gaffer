# -*- coding: utf-8 -*-
"""OpenPype startup script.

Add OpenPype Menu entries to GafferUI
See: http://www.gafferhq.org/documentation/0.53.0.0/Tutorials/Scripting/AddingAMenuItem/index.html  # noqa

"""
from openpype.pipeline import install_host
from ayon_gaffer.api import GafferHost, set_root

import GafferUI

# Make sure linter ignores undefined `application`, Gaffer startup provides it
application = application # noqa


def _install_ayon_menu():
    from openpype.tools.utils import host_tools
    definition = GafferUI.ScriptWindow.menuDefinition(application)

    def get_main_window(menu):
        script_window = menu.ancestor(GafferUI.ScriptWindow)
        set_root(script_window.scriptNode())     # todo: avoid hack
        return script_window._qtWidget()
    
    definition.append(
        "/OpenPype/Create...",
        {"command": lambda menu: host_tools.show_publisher(
            parent=get_main_window(menu),
            tab="create")}
    )

    definition.append(
        "/AYON/Load...",
        {"command": lambda menu: host_tools.show_loader(
            parent=get_main_window(menu),
            use_context=True)}
    )
    definition.append(
        "/AYON/Publish...",
        {"command": lambda menu: host_tools.show_publisher(
            parent=get_main_window(menu),
            tab="publish")}
    )
    definition.append(
        "/AYON/Manage...",
        {"command": lambda menu: host_tools.show_scene_inventory(
            parent=get_main_window(menu))}
    )
    definition.append(
        "/AYON/Library...",
        {"command": lambda menu: host_tools.show_library_loader(
            parent=get_main_window(menu))}
    )

    # Divider
    definition.append("/AYON/WorkFilesDivider", {"divider": True})

    definition.append(
        "/AYON/Work Files...",
        {"command": lambda menu: host_tools.show_workfiles(
            parent=get_main_window(menu))}
    )


def _install_ayon():
    print("Installing AYON ...")
    install_host(GafferHost(application))


_install_ayon()
_install_ayon_menu()
