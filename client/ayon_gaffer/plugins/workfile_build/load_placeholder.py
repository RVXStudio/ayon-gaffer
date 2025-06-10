import imath

from ayon_core.pipeline.workfile.workfile_template_builder import (
    LoadPlaceholderItem,
    PlaceholderLoadMixin,
)
from ayon_gaffer.api import get_root
from ayon_gaffer.api.lib import get_full_name

from ayon_gaffer.api.workfile_template_builder import GafferPlaceholderPlugin


class GafferPlaceholderLoadPlugin(GafferPlaceholderPlugin, PlaceholderLoadMixin):
    identifier = "gaffer.load"
    label = "Gaffer load"

    def _parse_placeholder_node_data(self, node):
        placeholder_data = super(GafferPlaceholderLoadPlugin, self)._parse_placeholder_node_data(node)

        node_full_name = get_full_name(node)
        placeholder_data["group_name"] = node_full_name.rpartition(".")[0]
        placeholder_data["last_loaded"] = []
        placeholder_data["delete"] = False
        return placeholder_data

    def _get_loaded_repre_ids(self):
        loaded_representation_ids = self.builder.get_shared_populate_data("loaded_representation_ids")
        if loaded_representation_ids is None:
            loaded_representation_ids = set()
            for node in get_root().children():
                if "repre_id" in node.knobs():
                    loaded_representation_ids.add(node.knob("repre_id").getValue())

            self.builder.set_shared_populate_data("loaded_representation_ids", loaded_representation_ids)
        return loaded_representation_ids

    def _before_placeholder_load(self, placeholder):
        placeholder.data["nodes_init"] = get_root().children()

    def _before_repre_load(self, placeholder, representation):
        placeholder.data["last_repre_id"] = representation["id"]

    def collect_placeholders(self):
        output = []
        scene_placeholders = self._collect_scene_placeholders()
        for node_name, node in scene_placeholders.items():
            plugin_identifier_knob = node["user"]["plugin_identifier"]
            if plugin_identifier_knob is None or plugin_identifier_knob.getValue() != self.identifier:
                continue

            placeholder_data = self._parse_placeholder_node_data(node)
            output.append(LoadPlaceholderItem(node_name, placeholder_data, self))

        return output

    def populate_placeholder(self, placeholder):
        self.populate_load_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        repre_ids = self._get_loaded_repre_ids()
        self.populate_load_placeholder(placeholder, repre_ids)

    def get_placeholder_options(self, options=None):
        return self.get_load_plugin_options(options)
