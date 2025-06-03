import collections
import Gaffer, GafferUI, imath
from ayon_core.pipeline import registered_host
from ayon_core.pipeline.workfile.workfile_template_builder import (
    AbstractTemplateBuilder,
    PlaceholderPlugin,
)
from ayon_core.tools.workfile_template_build import WorkfileBuildPlaceholderDialog
from .pipeline import imprint
from ayon_gaffer.api import get_root

PLACEHOLDER_SET = "PLACEHOLDERS_SET"


def get_main_window():
    sw = GafferUI.ScriptWindow(get_root())
    return sw._qtWidget()


class GafferTemplateBuilder(AbstractTemplateBuilder):
    """Concrete implementation of AbstractTemplateBuilder for gaffer"""

    def import_template(self, path):
        """Import template into current scene.
        Block if a template is already loaded.

        Args:
            path (str): A path to current template (usually given by
            get_template_preset implementation)

        Returns:
            bool: Whether the template was successfully imported or not
        """

        # TODO check if the template is already imported
        script_node = get_root()
        script_node.importFile(path, continueOnError=True)

        return True


class GafferPlaceholderPlugin(PlaceholderPlugin):
    node_color = imath.Color4f(0.8, 0.393973, 0.0342622, 1)  # todo get the right color from nuke

    def _collect_scene_placeholders(self):
        # Cache placeholder data to shared data
        placeholder_nodes = self.builder.get_shared_populate_data("placeholder_nodes")
        if placeholder_nodes is None:
            placeholder_nodes = {}
            all_groups = collections.deque()
            all_groups.append(get_root())
            while all_groups:
                group = all_groups.popleft()
                for node in group.children():
                    if isinstance(node, Gaffer.Box):
                        all_groups.append(node)

                    if "user" not in node:
                        continue

                    if "is_placeholder" not in node["user"] or not node["user"]["is_placeholder"].getValue():
                        continue

                    if "empty" in node["user"] and node["user"]["empty"].getValue():
                        continue

                    placeholder_nodes[node.fullName()] = node

            self.builder.set_shared_populate_data("placeholder_nodes", placeholder_nodes)
        return placeholder_nodes

    def create_placeholder(self, placeholder_data):
        placeholder_data["plugin_identifier"] = self.identifier

        script = get_root()
        placeholder = Gaffer.Node()

        script.addChild(placeholder)

        placeholder.setName("PLACEHOLDER")
        # placeholder["color"].setValue(self.node_color)  # todo color is not available on Node

        imprint(placeholder, placeholder_data)
        imprint(placeholder, {"is_placeholder": True})
        # placeholder.knob("is_placeholder").setVisible(False)  # todo set metadata

    def update_placeholder(self, placeholder_item, placeholder_data):
        node = get_root()[placeholder_item.scene_identifier]
        imprint(node, placeholder_data)

    def _parse_placeholder_node_data(self, node):
        placeholder_data = {}
        for key in self.get_placeholder_keys():
            plug = node["user"][key]
            value = None
            if plug is not None:
                value = plug.getValue()
            placeholder_data[key] = value
        return placeholder_data

    def delete_placeholder(self, placeholder):
        """Remove placeholder if building was successful"""
        # todo check if the placeholder is empty
        node = get_root()[placeholder.scene_identifier]
        del node


def build_workfile_template(*args, **kwargs):
    builder = GafferTemplateBuilder(registered_host())
    built_template = builder.build_template()

    # todo set the context when the scene is built
    # if built_template:
    # set all settings to shot context default
    # WorkfileSettings().set_context_settings()


def update_workfile_template(*args):
    builder = GafferTemplateBuilder(registered_host())
    builder.rebuild_template()


def create_placeholder(main_window):
    host = registered_host()
    builder = GafferTemplateBuilder(host)
    window = WorkfileBuildPlaceholderDialog(host, builder, parent=main_window)

    window.show()


def update_placeholder(script_node):
    host = registered_host()
    builder = GafferTemplateBuilder(host)
    placeholder_items_by_id = {
        placeholder_item.scene_identifier: placeholder_item for placeholder_item in builder.get_placeholders()
    }
    placeholder_items = []
    for node in script_node.selection():
        node_name = node.fullName()
        if node_name in placeholder_items_by_id:
            placeholder_items.append(placeholder_items_by_id[node_name])

    # TODO show UI at least
    if len(placeholder_items) == 0:
        raise ValueError("No node selected")

    if len(placeholder_items) > 1:
        raise ValueError("Too many selected nodes")

    placeholder_item = placeholder_items[0]
    window = WorkfileBuildPlaceholderDialog(host, builder, parent=get_main_window())
    window.set_update_mode(placeholder_item)
    window.exec_()
