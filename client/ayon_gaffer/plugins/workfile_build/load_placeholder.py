import Gaffer

from ayon_core.pipeline.workfile.workfile_template_builder import (
    LoadPlaceholderItem,
    PlaceholderLoadMixin,
)
from ayon_gaffer.api import get_root
from ayon_gaffer.api.lib import get_nodes_bbox, get_nodes_by_names, get_full_name, get_names_from_nodes
from ayon_gaffer.api.pipeline import imprint

from ayon_gaffer.api.workfile_template_builder import GafferPlaceholderPlugin


class GafferPlaceholderLoadPlugin(GafferPlaceholderPlugin, PlaceholderLoadMixin):
    identifier = "gaffer.load"
    label = "Gaffer load"

    def _parse_placeholder_node_data(self, node):
        placeholder_data = super(GafferPlaceholderLoadPlugin, self)._parse_placeholder_node_data(node)

        nb_children = 0
        if "nb_children" in node["user"]:
            nb_children = int(node["user"]["nb_children"].getValue())
        placeholder_data["nb_children"] = nb_children

        siblings = []
        if "siblings" in node["user"]:
            siblings = node["user"]["siblings"].values()
        placeholder_data["siblings"] = siblings

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
            # TODO do data validations and maybe updgrades if are invalid
            output.append(LoadPlaceholderItem(node_name, placeholder_data, self))

        return output

    def populate_placeholder(self, placeholder):
        self.populate_load_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        repre_ids = self._get_loaded_repre_ids()
        self.populate_load_placeholder(placeholder, repre_ids)

    def get_placeholder_options(self, options=None):
        return self.get_load_plugin_options(options)

    def post_placeholder_process(self, placeholder, failed):
        """Cleanup placeholder after load of its corresponding representations.

        Args:
            placeholder (PlaceholderItem): Item which was just used to load
                representation.
            failed (bool): Loading of representation failed.
        """
        # deselect all selected nodes
        root = get_root()
        # todo
        import sys;sys.path.append("/opt/pycharm-2025.1.1.1/debug-eggs/pydevd-pycharm.egg")
        import pydevd_pycharm
        pydevd_pycharm.settrace('localhost', port=3000, stdoutToServer=True, stderrToServer=True)
        placeholder_node = root[placeholder.scene_identifier]

        # getting the latest nodes added
        # TODO get from shared populate data!
        nodes_init = placeholder.data["nodes_init"]
        nodes_loaded = list(set(root.children()) - set(nodes_init))
        self.log.debug("Loaded nodes: {}".format(nodes_loaded))
        if not nodes_loaded:
            return

        placeholder.data["delete"] = True

        placeholder.data["last_loaded"] = nodes_loaded

        # positioning of the loaded nodes
        min_x, min_y, _, _ = get_nodes_bbox(nodes_loaded)
        for node in nodes_loaded:
            # todo use graph.GetNodePosition instead of __uiPosition because it is not created at this point
            xpos = (node["__uiPosition"]["x"].getValue() - min_x) + placeholder_node["__uiPosition"]["x"].getValue()
            ypos = (node["__uiPosition"]["y"].getValue() - min_y) + placeholder_node["__uiPosition"]["y"].getValue()
            node.setXYpos(xpos, ypos)

        if placeholder.data.get("keep_placeholder"):
            self._imprint_siblings(placeholder)

        if placeholder.data["nb_children"] == 0:
            # save initial nodes positions and dimensions, update them
            # and set inputs and outputs of loaded nodes
            if placeholder.data.get("keep_placeholder"):
                self._imprint_inits()
                self._update_nodes(placeholder, root.children(), nodes_loaded)

            self._set_loaded_connections(placeholder)

        elif placeholder.data["siblings"]:
            # create copies of placeholder siblings for the new loaded nodes,
            # set their inputs and outputs and update all nodes positions and
            # dimensions and siblings names

            siblings = get_nodes_by_names(placeholder.data["siblings"])
            copies = self._create_sib_copies(placeholder)
            new_nodes = list(copies.values())  # copies nodes
            self._update_nodes(new_nodes, nodes_loaded)
            placeholder_node.removeKnob(placeholder_node.knob("siblings"))
            new_nodes_name = get_names_from_nodes(new_nodes)
            imprint(placeholder_node, {"siblings": new_nodes_name})
            self._set_copies_connections(placeholder, copies)

            self._update_nodes(root.children(), new_nodes + nodes_loaded, 20)

            new_siblings = get_names_from_nodes(new_nodes)
            placeholder.data["siblings"] = new_siblings

        else:
            # if the placeholder doesn't have siblings, the loaded
            # nodes will be placed in a free space

            xpointer, ypointer = find_free_space_to_paste_nodes(nodes_loaded, direction="bottom", offset=200)
            # todo is it really needed for gaffer
            node = Gaffer.Node("PLACEHOLDER")
            reset_selection()
            del node
            for node in nodes_loaded:
                xpos = (node["__uiPosition"]["x"].getValue() - min_x) + xpointer
                ypos = (node["__uiPosition"]["y"].getValue() - min_y) + ypointer
                node.setXYpos(xpos, ypos)

        placeholder.data["nb_children"] += 1
        reset_selection()

    def _imprint_siblings(self, placeholder):
        """
        - add siblings names to placeholder attributes (nodes loaded with it)
        - add Id to the attributes of all the other nodes
        """

        loaded_nodes = placeholder.data["last_loaded"]
        loaded_nodes_set = set(loaded_nodes)
        data = {"repre_id": str(placeholder.data["last_repre_id"])}

        for node in loaded_nodes:
            node_knobs = node.knobs()
            if "builder_type" not in node_knobs:
                # save the id of representation for all imported nodes
                imprint(node, data)
                node.knob("repre_id").setVisible(False)
                continue

            if "is_placeholder" not in node_knobs or (
                "is_placeholder" in node_knobs and node.knob("is_placeholder").value()
            ):
                siblings = list(loaded_nodes_set - {node})
                siblings_name = get_names_from_nodes(siblings)
                siblings = {"siblings": siblings_name}
                imprint(node, siblings)

    def _imprint_inits(self):
        """Add initial positions and dimensions to the attributes"""

        for node in get_root().children():
            imprint(
                node, {"x_init": node["__uiPosition"]["x"].getValue(), "y_init": node["__uiPosition"]["y"].getValue()}
            )
            width = node.screenWidth()
            height = node.screenHeight()
            if "bdwidth" in node.knobs():
                imprint(node, {"w_init": width, "h_init": height})
                node.knob("w_init").setVisible(False)
                node.knob("h_init").setVisible(False)

    def _update_nodes(self, placeholder, nodes, considered_nodes, offset_y=None):
        """Adjust backdrop nodes dimensions and positions.

        Considering some nodes sizes.

        Args:
            nodes (list): list of nodes to update
            considered_nodes (list): list of nodes to consider while updating
                positions and dimensions
            offset (int): distance between copies
        """

        placeholder_node = get_root()[placeholder.scene_identifier]

        min_x, min_y, max_x, max_y = get_nodes_bbox(considered_nodes)

        diff_x = diff_y = 0
        contained_nodes = []  # for backdrops

        if offset_y is None:
            width_ph = placeholder_node.screenWidth()
            height_ph = placeholder_node.screenHeight()
            diff_y = max_y - min_y - height_ph
            diff_x = max_x - min_x - width_ph
            contained_nodes = [placeholder_node]
            min_x = placeholder_node["__uiPosition"]["x"].getValue()
            min_y = placeholder_node["__uiPosition"]["y"].getValue()
        else:
            siblings = get_nodes_by_names(placeholder.data["siblings"])
            minX, _, maxX, _ = get_nodes_bbox(siblings)
            diff_y = max_y - min_y + 20
            diff_x = abs(max_x - min_x - maxX + minX)
            contained_nodes = considered_nodes

        if diff_y <= 0 and diff_x <= 0:
            return

        for node in nodes:

            if node == placeholder_node or node in considered_nodes:
                continue

            if not isinstance(node, nuke.BackdropNode) or (
                isinstance(node, nuke.BackdropNode) and not set(contained_nodes) <= set(node.getNodes())
            ):
                if offset_y is None and node["__uiPosition"]["x"].getValue() >= min_x:
                    node.setXpos(node["__uiPosition"]["x"].getValue() + diff_x)

                if node["__uiPosition"]["y"].getValue() >= min_y:
                    node.setYpos(node["__uiPosition"]["y"].getValue() + diff_y)

            else:
                width = node.screenWidth()
                height = node.screenHeight()
                node.knob("bdwidth").setValue(width + diff_x)
                node.knob("bdheight").setValue(height + diff_y)

            refresh_node(node)

    def _set_loaded_connections(self, placeholder):
        """
        set inputs and outputs of loaded nodes"""

        placeholder_node = get_root()[placeholder.scene_identifier]
        input_node, output_node = get_group_io_nodes(placeholder.data["last_loaded"])
        for node in placeholder_node.dependent():
            for idx in range(node.inputs()):
                if node.input(idx) == placeholder_node and output_node:
                    node.setInput(idx, output_node)

        for node in placeholder_node.dependencies():
            for idx in range(placeholder_node.inputs()):
                if placeholder_node.input(idx) == node and input_node:
                    input_node.setInput(0, node)

    def _create_sib_copies(self, placeholder):
        """creating copies of the palce_holder siblings (the ones who were
        loaded with it) for the new nodes added

        Returns :
            copies (dict) : with copied nodes names and their copies
        """

        copies = {}
        siblings = get_nodes_by_names(placeholder.data["siblings"])
        for node in siblings:
            new_node = duplicate_node(node)

            x_init = int(new_node.knob("x_init").getValue())
            y_init = int(new_node.knob("y_init").getValue())
            new_node.setXYpos(x_init, y_init)
            if isinstance(new_node, nuke.BackdropNode):
                w_init = new_node.knob("w_init").getValue()
                h_init = new_node.knob("h_init").getValue()
                new_node.knob("bdwidth").setValue(w_init)
                new_node.knob("bdheight").setValue(h_init)
                refresh_node(node)

            if "repre_id" in node.knobs().keys():
                node.removeKnob(node.knob("repre_id"))
            copies[node.name()] = new_node
        return copies

    def _set_copies_connections(self, placeholder, copies):
        """Set inputs and outputs of the copies.

        Args:
            copies (dict): Copied nodes by their names.
        """

        last_input, last_output = get_group_io_nodes(placeholder.data["last_loaded"])
        siblings = get_nodes_by_names(placeholder.data["siblings"])
        siblings_input, siblings_output = get_group_io_nodes(siblings)
        copy_input = copies[siblings_input.name()]
        copy_output = copies[siblings_output.name()]

        for node_init in siblings:
            if node_init == siblings_output:
                continue

            node_copy = copies[node_init.name()]
            for node in node_init.dependent():
                for idx in range(node.inputs()):
                    if node.input(idx) != node_init:
                        continue

                    if node in siblings:
                        copies[node.name()].setInput(idx, node_copy)
                    else:
                        last_input.setInput(0, node_copy)

            for node in node_init.dependencies():
                for idx in range(node_init.inputs()):
                    if node_init.input(idx) != node:
                        continue

                    if node_init == siblings_input:
                        copy_input.setInput(idx, node)
                    elif node in siblings:
                        node_copy.setInput(idx, copies[node.name()])
                    else:
                        node_copy.setInput(idx, last_output)

        siblings_input.setInput(0, copy_output)
