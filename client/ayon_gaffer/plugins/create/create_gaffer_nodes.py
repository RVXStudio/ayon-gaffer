from ayon_gaffer.api.lib import make_box, set_node_color
from ayon_gaffer.api import plugin

import Gaffer


class CreateGafferNodes(plugin.GafferCreatorBase):
    identifier = "io.openpype.creators.gaffer.gaffernodes"
    label = "Gaffer Box"
    family = "gafferNodes"
    description = "Export Box node for referencing"
    icon = "gears"

    def _create_node(self,
                     subset_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:

        if len(self.selected_nodes) > 0:
            box_nodes = [node for node in self.selected_nodes
                         if node.typeName() == "Gaffer::Box"]

            if len(box_nodes) == 1 and len(self.selected_nodes) == 1:
                # we have one and just one box selected. So just mark
                # that for publish
                box_node = box_nodes[0]
                data = self._read(box_node)
                if data.get("id") == "pyblish.avalon.instance":
                    raise plugin.GafferCreatorError(
                        "This box is already being published!")
            else:
                # we have a mix of other nodes, group 'em up
                box_node = Gaffer.Box.create(script, self.selected_nodes)
                box_node.setName(subset_name)
        else:
            box_node = make_box(subset_name)
            script.addChild(box_node)

        # colorise boxes to be published
        # TODO: Use settings instead
        set_node_color(box_node, (0.788, 0.39, 0.22))

        return box_node
