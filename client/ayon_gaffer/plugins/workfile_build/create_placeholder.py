import Gaffer, imath
from ayon_core.pipeline.workfile.workfile_template_builder import (
    CreatePlaceholderItem,
    PlaceholderCreateMixin,
)
from ayon_gaffer.api.workfile_template_builder import GafferPlaceholderPlugin
from ayon_gaffer.api.pipeline import imprint
from ayon_gaffer.api import get_root
from ayon_gaffer.api.lib import get_full_name, get_io_plugs, copy_plug


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

    def create_placeholder(self, placeholder_data):
        placeholder_data["plugin_identifier"] = self.identifier

        script = get_root()

        placeholder = Gaffer.Node()

        creators_by_name = self.builder.get_creators_by_name()

        creator = creators_by_name.get(placeholder_data["creator"])
        if not creator:
            raise ValueError("Creator not found: {}".format(placeholder_data["creator"]))

        tmp_node = creator._create_node(product_name="tmp_node", pre_create_data={}, script=script)

        plugs = get_io_plugs(tmp_node)

        for source_plug in plugs:
            new_plug = copy_plug(source_plug, placeholder)
            flags = new_plug.getFlags()
            # add dynamic plug so it is serialized
            new_plug.setFlags(flags | Gaffer.Plug.Flags.Dynamic)


        script.removeChild(tmp_node)
        placeholder_name = placeholder_data['creator'].split('.')[-1]


        script.addChild(placeholder)

        placeholder.setName(f"PLACEHOLDER_{placeholder_name}")
        Gaffer.Metadata.registerValue(placeholder, "nodeGadget:color", imath.Color3f(0.6, 0.2, 0.2))

        imprint(placeholder, placeholder_data)
        imprint(placeholder, {"is_placeholder": True})

    def populate_placeholder(self, placeholder):
        self.populate_create_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        self.populate_create_placeholder(placeholder)

    def get_placeholder_options(self, options=None):
        return self.get_create_plugin_options(options)
