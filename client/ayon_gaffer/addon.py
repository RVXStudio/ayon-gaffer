import os
import copy
import sys
import platform
import tempfile
import json
import subprocess

import click
from qtpy import QtCore, QtWidgets, QtGui
import pyblish.api

from openpype.modules import (
    OpenPypeModule,
    ITrayModule,
    IPluginPaths,
    ILaunchHookPaths,
    IHostAddon
)
from openpype.lib import Logger
from openpype.settings import (
    get_system_settings,
    get_project_settings,
    get_local_settings
)
from openpype.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path
)

from openpype.lib import register_event_callback
from openpype.lib.execute import (
    get_linux_launcher_args
)
# from . import lib
#import rvx_ayon.luts
# import rvx_core.utils
import ayon_api
from functools import partial

GAFFER_HOST_DIR = os.path.dirname(os.path.abspath(__file__))
_URL_NOT_SET = object()


class GafferAddon(
    OpenPypeModule,
    IPluginPaths,
    ILaunchHookPaths,
    IHostAddon,
):
    name = "gaffer"
    host_name = "gaffer"
    enabled = True

    def initialize(self, module_settings):
        self.enabled = True

    def add_implementation_envs(self, env, _app):
        # Add requirements to GAFFER_EXTENSION_PATHS
        startup_path = GAFFER_HOST_DIR
        if env.get("GAFFER_EXTENSION_PATHS"):
            startup_path += os.pathsep + env["GAFFER_EXTENSION_PATHS"]

        env["GAFFER_EXTENSION_PATHS"] = startup_path

    def get_launch_hook_paths(self, app):
        if app.host_name != self.host_name:
            return []
        return [
            os.path.join(GAFFER_HOST_DIR, "hooks")
        ]

    def get_workfile_extensions(self):
        return [".gfr"]

    def get_plugin_paths(self):
        return {}

    def tray_init(self):
        # doing nothing in here for now
        pass

    def tray_start(self):
        pass

    def tray_exit(self):
        pass

    def tray_menu(self, tray_menu):
        pass


@click.group(GafferAddon.name, help="Gaffer addon related commands.")
def cli_main():
    pass
