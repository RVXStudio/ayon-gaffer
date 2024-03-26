from ayon_gaffer.api import (
    GafferCreator,
    get_root
)

from ayon_gaffer.api.lib import make_box

class CreateBox(GafferCreator):
    """Add Publishable Backdrop"""

    identifier = "create_backdrop"
    label = "Nukenodes (backdrop)"
    family = "nukenodes"
    icon = "file-archive-o"
    maintain_selection = True

    # plugin attributes
    node_color = "0xdfea5dff"

    def create_instance_node(
        self,
        node_name,
        knobs=None,
        parent=None,
        node_type=None
    ):
        self.log.info(f"CREATING BOX {node_name}")
        boxnode = make_box(node_name)
        get_root().addChild(boxnode)
        return boxnode

    def create(self, subset_name, instance_data, pre_create_data):
        # make sure subset name is unique
        self.check_existing_subset(subset_name)

        instance = super(CreateBox, self).create(
            subset_name,
            instance_data,
            pre_create_data
        )

        return instance
