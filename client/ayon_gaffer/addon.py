import os

from ayon_core.addon import (
    AYONAddon, IHostAddon
)


from .version import __version__


GAFFER_HOST_DIR = os.path.dirname(os.path.abspath(__file__))
_URL_NOT_SET = object()


class GafferAddon(
    AYONAddon,
    IHostAddon,
):
    name = "gaffer"
    version = __version__
    host_name = "gaffer"
    enabled = True

    def initialize(self, module_settings):
        self.enabled = True

    def add_implementation_envs(self, env, _app):
        # Add requirements to GAFFER_EXTENSION_PATHS
        startup_path = os.path.join(GAFFER_HOST_DIR, "deploy")
        gaffer_deadline_path = os.path.join(startup_path, "GafferDeadline")
        ext_path = startup_path + os.pathsep + gaffer_deadline_path
        if env.get("GAFFER_EXTENSION_PATHS"):
            ext_path += os.pathsep + env["GAFFER_EXTENSION_PATHS"]

        env["GAFFER_EXTENSION_PATHS"] = ext_path

        gaffer_deadline_dep_path = os.path.join(
            gaffer_deadline_path, "gaffer_batch_dependency.py")

        env["DEADLINE_DEPENDENCY_SCRIPT_PATH"] = gaffer_deadline_dep_path

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
