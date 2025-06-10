import Gaffer

from ayon_core.pipeline.workfile.workfile_template_builder import (
    CreatePlaceholderItem,
    PlaceholderCreateMixin,
)
from ayon_gaffer.api.workfile_template_builder import GafferPlaceholderPlugin

from ayon_gaffer.api import get_root
from ayon_gaffer.api.lib import get_full_name

class GafferPlaceholderCreatePlugin(GafferPlaceholderPlugin, PlaceholderCreateMixin):
    identifier = "gaffer.create"
    label = "Gaffer Create"

    def _parse_placeholder_node_data(self, node: Gaffer.Node):
        placeholder_data = super(GafferPlaceholderCreatePlugin, self)._parse_placeholder_node_data(node)

        node_full_name = get_full_name(node)
        placeholder_data["group_name"] = node_full_name.rpartition(".")[0]
        placeholder_data["last_loaded"] = []
        placeholder_data["delete"] = False
        return placeholder_data

    def _before_instance_create(self, placeholder):
        placeholder.data["nodes_init"] = get_root().children()

    def collect_placeholders(self):
        output = []
        scene_placeholders = self._collect_scene_placeholders()
        for node_name, node in scene_placeholders.items():
            plug_identifier = node["user"]["plugin_identifier"]

            if plug_identifier is None or plug_identifier.getValue() != self.identifier:
                continue

            placeholder_data = self._parse_placeholder_node_data(node)

            output.append(CreatePlaceholderItem(node_name, placeholder_data, self))

        return output

    def populate_placeholder(self, placeholder):
        self.populate_create_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        self.populate_create_placeholder(placeholder)

    def get_placeholder_options(self, options=None):
        return self.get_create_plugin_options(options)
