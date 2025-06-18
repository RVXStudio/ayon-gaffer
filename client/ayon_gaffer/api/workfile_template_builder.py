import collections
import Gaffer, GafferUI, imath
from ayon_core.pipeline import registered_host
from ayon_core.pipeline.workfile.workfile_template_builder import (
    AbstractTemplateBuilder,
    PlaceholderPlugin,
)
from ayon_core.tools.workfile_template_build import WorkfileBuildPlaceholderDialog
from .pipeline  import get_root
from ayon_gaffer.api.lib import get_full_name, get_plug_connection_mapping


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

        script_node = get_root()
        script_node.importFile(path, continueOnError=True)

        return True


class GafferPlaceholderPlugin(PlaceholderPlugin):

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

                    placeholder_nodes[get_full_name(node)] = node

            self.builder.set_shared_populate_data("placeholder_nodes", placeholder_nodes)
        return placeholder_nodes



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
        root = get_root()
        try:
            node = root[placeholder.scene_identifier]
            root.removeChild(node)
        except KeyError:
            self.log.error("Placeholder node not found: {}".format(placeholder.scene_identifier))

    def post_placeholder_process(self, placeholder, failed):
        """Cleanup placeholder after load of its corresponding representations.

        Args:
            placeholder (PlaceholderItem): Item which was just used to load
                representation.
            failed (bool): Loading of representation failed.
        """
        root = get_root()
        placeholder_node = root[placeholder.scene_identifier]
        nodes_init = placeholder.data["nodes_init"]
        nodes_loaded = list(set(root.children()) - set(nodes_init))
        if not nodes_loaded:
            self.log.error("No nodes loaded after placeholder processing, nothing to connect.")
            return

        self.log.debug("Loaded nodes: {}".format(nodes_loaded))

        node_loaded = nodes_loaded[0]

        def find_matching_source_plug(plug, node):
            name = plug.getName()
            if name in node:
                return node[name]
            elif plug.parent().typeName() == "Gaffer::ArrayPlug":
                if plug.parent().getName() in node:
                    return node[plug.parent().getName()][name]
            return plug

        plug_mapping = get_plug_connection_mapping(placeholder_node)

        for connection in plug_mapping:
            in_plug = connection["in"]
            if placeholder_node.fullName() in in_plug.fullName():
                in_plug = find_matching_source_plug(connection["in"], node_loaded)

            out_plug = connection["out"]
            if placeholder_node.fullName() in out_plug.fullName():
                out_plug = find_matching_source_plug(connection["out"], node_loaded)

            out_plug.setInput(in_plug)


def build_workfile_template(*args, **kwargs):
    builder = GafferTemplateBuilder(registered_host())
    builder.build_template()


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
        node_name = get_full_name(node)
        if node_name in placeholder_items_by_id:
            placeholder_items.append(placeholder_items_by_id[node_name])

    if len(placeholder_items) == 0:
        raise ValueError("No node selected")

    if len(placeholder_items) > 1:
        raise ValueError("Too many selected nodes")

    placeholder_item = placeholder_items[0]
    window = WorkfileBuildPlaceholderDialog(host, builder, parent=get_main_window())
    window.set_update_mode(placeholder_item)
    window.exec_()
