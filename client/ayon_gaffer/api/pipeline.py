# -*- coding: utf-8 -*-
"""Pipeline tools for OpenPype Gaffer integration."""
import os
import sys
import json

import Gaffer  # noqa
import imath

import ayon_api
from ayon_core.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from ayon_gaffer.api.nodes import RenderLayerNode

import pyblish.api

from ayon_core.pipeline import (
    register_creator_plugin_path,
    register_loader_plugin_path,
    register_inventory_action_path,
    AVALON_CONTAINER_ID,
    AYON_CONTAINER_ID,
    get_current_folder_path,
    get_current_task_name,
    register_workfile_build_plugin_path,
    registered_host,
)
from ayon_gaffer import GAFFER_HOST_DIR
import ayon_gaffer.api.nodes
import ayon_gaffer.api.lib
from ayon_core.settings import get_current_project_settings
from ayon_core.lib import Logger, StringTemplate

import ayon_gaffer.api.nodes

log = Logger.get_logger("ayon_gaffer.api.pipeline")

PLUGINS_DIR = os.path.join(GAFFER_HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")
WORKFILE_BUILD_PATH = os.path.join(PLUGINS_DIR, "workfile_build")
DEADLINE_LIMIT_GROUPS = []
AYON_ATTR_GROUP_KEY = "ayon_attr_group"

self = sys.modules[__name__]
self.root = None

# A prefix used for storing JSON blobs in string plugs
JSON_PREFIX = "JSON:::"


def set_root(root: Gaffer.ScriptNode):
    self.root = root


def get_root() -> Gaffer.ScriptNode:
    return self.root


class GafferHost(HostBase, IWorkfileHost, ILoadHost, IPublishHost):
    name = "gaffer"

    _context_plug = "ayon_context"

    def __init__(self, application):
        super(GafferHost, self).__init__()
        self.application = application

    def install(self):
        pyblish.api.register_host("gaffer")

        pyblish.api.register_plugin_path(PUBLISH_PATH)
        register_loader_plugin_path(LOAD_PATH)
        register_creator_plugin_path(CREATE_PATH)
        register_inventory_action_path(INVENTORY_PATH)
        register_workfile_build_plugin_path(WORKFILE_BUILD_PATH)
        log.info("Registering paths")
        log.info(PUBLISH_PATH)
        log.info(LOAD_PATH)
        log.info(CREATE_PATH)
        log.info(INVENTORY_PATH)
        log.info(WORKFILE_BUILD_PATH)

        self._register_callbacks()

    def has_unsaved_changes(self):
        script = get_root()
        return script["unsavedChanges"].getValue()

    def get_workfile_extensions(self):
        return [".gfr"]

    def save_workfile(self, dst_path=None):
        if not dst_path:
            dst_path = self.get_current_workfile()

        dst_path = dst_path.replace("\\", "/")

        script = get_root()
        script.serialiseToFile(dst_path)
        script["fileName"].setValue(dst_path)
        script["unsavedChanges"].setValue(False)

        application = script.ancestor(Gaffer.ApplicationRoot)
        if application:
            import GafferUI.FileMenu
            GafferUI.FileMenu.addRecentFile(application, dst_path)

        self.update_project_root_directory(script)

        return dst_path

    def open_workfile(self, filepath):
        if not os.path.exists(filepath):
            raise RuntimeError("File does not exist: {}".format(filepath))

        script = get_root()
        if script:
            script["fileName"].setValue(filepath)
            script.load()
        self._on_scene_new(script.ancestor(Gaffer.ScriptContainer), script)
        return filepath

    def get_current_workfile(self):
        script = get_root()
        return script["fileName"].getValue()

    def get_containers(self):
        script = get_root()

        required = [
            "schema", "id", "name", "namespace", "representation", "loader"
        ]
        nodes = []
        ayon_gaffer.api.lib.traverse_nodegraph_skipping_nested_references(script, nodes)
        for node in nodes:
            if "user" not in node:
                # No user attributes
                continue

            user = node["user"]
            if any(key not in user for key in required):
                continue

            if user["id"].getValue() not in {AYON_CONTAINER_ID, AVALON_CONTAINER_ID}:
                continue
            container = {
                key: user[key].getValue() for key in required
            }
            node_name = node.fullName().replace(
                node.scriptNode().fullName(), "").strip(".")
            container["objectName"] = node_name
            container["_node"] = node
            if "version_freeze" in node["user"]:
                container["version_freeze"] = user["version_freeze"].getValue()

            yield container

    def update_context_data(self, data, changes):
        """Store context data as single JSON blob in script's user data"""
        script = get_root()
        data_str = json.dumps(data)

        # Always override the full plug - even if it already exists
        script["user"][self._context_plug] = Gaffer.StringPlug(
            defaultValue=data_str,
            flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
        )

    def get_context_data(self):
        script = get_root()
        if "user" in script and self._context_plug in script["user"]:
            data_str = script["user"][self._context_plug].getValue()
            return json.loads(data_str)
        return {}

    def _register_callbacks(self):
        scripts_list = self.application.root()["scripts"]
        scripts_list.childAddedSignal().connect(self._on_scene_new,
                                                scoped=False)

    def update_project_root_directory(self, script_node):
        log.info("updating project root directory")
        script_node['variables']['projectRootDirectory']['value'].setValue(
            self.work_root(os.environ))  # noqa

    def update_root_context_variables(self, script_node):
        ctxt = self.get_current_context()

        ayon_gaffer.api.lib.update_root_context_variables(
            script_node,
            ctxt["project_name"],
            ctxt["folder_path"]
        )

    def update_ocio_settings(self, script_node):
        imageio_config = get_current_project_settings().get("gaffer", {}).get("imageio", {})
        color_space = imageio_config.get("working_color_space", None)
        colorspace_display_transform = imageio_config.get("colorspace_display_transform", None)

        if color_space:
            script_node['openColorIO']['workingSpace'].setValue(str(color_space))

        if colorspace_display_transform:
            script_node['openColorIO']['displayTransform'].setValue(str(colorspace_display_transform))

    def _on_scene_new(self, script_container, script_node):
        # Update the projectRootDirectory variable for new workfile scripts
        self.update_project_root_directory(script_node)
        self.update_root_context_variables(script_node)
        self.update_ocio_settings(script_node)
        ayon_gaffer.api.lib.create_multishot_context_vars(script_node)
        ayon_gaffer.api.lib.set_framerate(script_node)
        log.debug(f'Adding childAddedSignal to {script_node}')
        script_node.childAddedSignal().connect(
            self.connect_render_layer_signals,
            scoped=False
        )

        # since the childAddedSignal gets added after the initial scene is
        # loaded we need to manually trigger the connect render layer
        # signal for the renderlayer nodes in the scene
        for node in script_node.children(RenderLayerNode):
            self.connect_render_layer_signals(script_node, node)

        ayon_gaffer.api.nodes.check_boxnode_versions(script_node)

        build_on_scene_new = get_current_project_settings()["gaffer"].get("templated_workfile_build", {}).get("build_on_scene_new", True)
        if not build_on_scene_new:
            log.info("Skipping workfile build on scene new: Ayon settings build_on_scene_new is set to False")

        if os.path.exists(os.environ.get("AYON_LAST_WORKFILE")):
            log.info(f"$AYON_LAST_WORKFILE exists!, not creating template")
            return

        log.info("Building from template")
        try:
            self._build_from_template(script_node)
        except Exception as exc:
            log.error(f"Could not build from template. Exception: {exc}")

    def _build_from_template(self, script_node):
        set_root(script_node)
        from ayon_gaffer.api.workfile_template_builder import GafferTemplateBuilder

        builder = GafferTemplateBuilder(self)
        builder.build_template()

    def connect_render_layer_signals(self, script_node, new_node):
        if isinstance(new_node, RenderLayerNode):
            try:
                new_node.connect_signals()
                # new_node.update_outputs()
            except Exception as err:
                log.error(f"Could not connect signals for render layer"
                          f"{new_node}: {err}")


def imprint_container(node: Gaffer.Node,
                      name: str,
                      namespace: str,
                      context: dict,
                      loader: str = None):
    """Imprint a Loader with metadata

    Containerisation enables a tracking of version, author and origin
    for loaded assets.

    Arguments:
        node (Gaffer.Node): The node in Gaffer to imprint as container,
            usually a node loaded by a Loader.
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        context (dict): Asset information
        loader (str, optional): Name of loader used to produce this container.

    Returns:
        None

    """
    data = {
        "schema": "openpype:container-2.0",
        "id": AYON_CONTAINER_ID,
        "name": str(name),
        "namespace": str(namespace),
        "loader": str(loader),
        "representation": str(context["representation"]["id"]),
    }
    imprint(node, data)


def imprint(node: Gaffer.Node,
            data: dict,
            section: str = "Ayon",
            group: str = ""):
    """Store and persist data on a node as `user` data.

    Args:
        node (Gaffer.Node): The node to store the data on.
            This can also be the workfile's root script node.
        data (dict): The key, values to store.
            Any `dict` values will be treated as JSON data and stored as
            string with `JSON:::` as a prefix to the value.
        section (str): Used to register the plug into a subsection in
            the user data allowing them to group data together.

    Returns:

    """

    FLAGS = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
    log.info(f"Impringint ..")
    parent_plug = node["user"]
    if group:
        # check for the group plug
        if AYON_ATTR_GROUP_KEY not in node["user"].keys():
            # create it

            log.info(f"Creating group plug")
            group_plug = Gaffer.CompoundDataPlug(
                AYON_ATTR_GROUP_KEY, flags=FLAGS)

            group_data_plug = Gaffer.CompoundDataPlug(
                "group_data_plug", flags=FLAGS)
            attr_plug = Gaffer.NameValuePlug(
                group, group_data_plug, True, "groups", flags=FLAGS)
            group_plug.addChild(attr_plug)
            node["user"].addChild(group_plug)
            if section:
                Gaffer.Metadata.registerValue(
                    group_plug, "layout:section", section)

        for child in node["user"][AYON_ATTR_GROUP_KEY].children():
            # searching for existing group plug
            if child["name"].getValue() == group:
                parent_plug = child["value"]
                log.info(f"Found parent plug for {group}")
                break
        else:
            log.info(f"No parent plug group found, making it ...")
            group_data_plug = Gaffer.CompoundDataPlug(
                "group_data_plug", flags=FLAGS)
            attr_plug = Gaffer.NameValuePlug(
                group, group_data_plug, True, "groups", flags=FLAGS)
            node["user"][AYON_ATTR_GROUP_KEY].addChild(attr_plug)
            parent_plug = group_data_plug

    def key_exists(parent_plug, key, group):
        if group:
            for child in parent_plug.children():
                if child["name"].getValue() == key:
                    # ok, found the plug
                    return True
        if key in parent_plug:
            return True
        return False

    def set_exisinting_value(parent_plug, key, group):
        for child in parent_plug.children():
            if child["name"].getValue() == key:
                # ok, found the plug
                child["value"].setValue(value)

    def add_new_key(parent_plug, plug, key, group):
        nv_plug = Gaffer.NameValuePlug(key, plug, True, "value", flags=FLAGS)
        parent_plug.addChild(nv_plug)

    for key, value in data.items():
        # Dict to JSON
        if isinstance(value, dict):
            value = json.dumps(value)
            value = f"{JSON_PREFIX}{value}"

        if key_exists(parent_plug, key, group):
            # Set existing attribute
            try:
                if value is None:
                    value = ""
                if group:
                    set_exisinting_value(parent_plug, key, value)
                else:
                    node["user"][key].setValue(value)
                continue
            except Exception:
                # If an exception occurs then we'll just replace the key
                # with a new plug (likely types have changed)
                log.warning("Unable to set %s attribute %s to value %s (%s). "
                            "Likely there is a value type mismatch. "
                            "Plug will be replaced.",
                            node.getName(), key, value, type(value),
                            exc_info=sys.exc_info())
                pass

        if value is None:
            value = "<None>"

        # Generate new plug with value as default value
        if isinstance(value, str):
            plug = Gaffer.StringPlug(key, defaultValue=value, flags=FLAGS)
        elif isinstance(value, bool):
            plug = Gaffer.BoolPlug(key, defaultValue=value, flags=FLAGS)
        elif isinstance(value, float):
            plug = Gaffer.FloatPlug(key, defaultValue=value, flags=FLAGS)
        elif isinstance(value, int):
            plug = Gaffer.IntPlug(key, defaultValue=value, flags=FLAGS)
        else:
            raise TypeError(
                f"Unsupported value type: {type(value)} -> {value}"
            )

        if section:
            Gaffer.Metadata.registerValue(plug, "layout:section", section)

        if group:
            add_new_key(parent_plug, plug, key, value)
        else:
            parent_plug[key] = plug


def get_context_label():
    return "{0}, {1}".format(
        get_current_folder_path(),
        get_current_task_name()
    )


def get_boxnode_paths_from_settings():
    """
    Fetch the current settings and resolve the node preset paths with the
    current environment.

    Returns: list
    """
    paths = get_current_project_settings()["gaffer"]["node_preset_paths"]
    env = os.environ.copy()
    boxnode_paths = []
    for boxpath in paths:
        log.debug(f"Adding boxnode path: {boxpath}")
        template = StringTemplate(boxpath)
        resolved_path = template.format(env)
        boxnode_paths.append(resolved_path)
    return boxnode_paths


def register_boxnode_paths_from_settings():
    """
    Get the extra boxnode paths from settings and register them.
    """
    boxnode_paths = get_boxnode_paths_from_settings()
    for boxnode_path in boxnode_paths:
        ayon_gaffer.api.nodes.register_boxnode_path(boxnode_path)
        log.info(f"Added [{boxnode_path}] to boxnode paths")


def _set_annotation(node, representation_id):
    try:
        project_name = os.environ.get("AYON_PROJECT_NAME")
        rep = ayon_api.get_representation_by_id(project_name, representation_id)
        version_id = rep["versionId"]
        version = ayon_api.get_version_by_id(project_name, version_id)
        product_id = version["productId"]
        current_version = version["version"]

        last_version = ayon_api.get_last_version_by_product_id(project_name, product_id)
        Gaffer.Metadata.registerValue(node, 'annotation:user:text', "v{:03d}".format(current_version))
        if current_version != last_version["version"]:
            Gaffer.Metadata.registerValue(node, 'annotation:user:color', imath.Color3f(0.55, 0.25, 0.25))
        else:
            Gaffer.Metadata.registerValue(node, 'annotation:user:color', imath.Color3f(0.25, 0.55, 0.25))
    except Exception as e:
        print(e)


def update_annotations(node):
    if "representation" not in node["user"]:
        return

    _set_annotation(node, node["user"]["representation"].getValue())


def update_annotations_on_all_nodes():
    host = registered_host()
    for container in host.get_containers():
        node = container["_node"]
        representation_id = container["representation"]

        _set_annotation(node, representation_id)