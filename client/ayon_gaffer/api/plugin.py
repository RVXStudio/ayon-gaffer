import json
from abc import abstractmethod

from openpype.pipeline import (
    Creator as NewCreator,
    CreatedInstance,
    CreatorError,
)
from openpype import AYON_SERVER_ENABLED

from openpype.lib import (
    BoolDef
)
from openpype.client import get_asset_by_name

from ayon_gaffer.api import (
    get_root,
)
from ayon_gaffer.api.pipeline import imprint, JSON_PREFIX
from ayon_gaffer.api.nodes import (
    AyonPublishTask,
    RenderLayerNode,
)

import Gaffer
import imath


def read(node):
    """Read all 'user' custom data on the node"""
    if "user" not in node:
        # No user attributes
        return {}
    return {
        plug.getName(): plug.getValue() for plug in node["user"]
    }


class CreatorImprintReadMixin:
    """Mixin providing _read and _imprint methods to be used by Creators."""

    attr_prefix = "openpype_"

    def _read(self, node: Gaffer.Node) -> dict:
        all_user_data = read(node)

        # Consider only data with the special attribute prefix
        # and strip off the prefix as for the resulting data
        prefix_len = len(self.attr_prefix)
        openpype_data = {}
        for key, value in all_user_data.items():
            if not key.startswith(self.attr_prefix):
                continue

            if isinstance(value, str) and value.startswith(JSON_PREFIX):
                value = value[len(JSON_PREFIX):]  # strip off JSON prefix
                value = json.loads(value)

            key = key[prefix_len:]      # strip off prefix
            openpype_data[key] = value

        openpype_data["instance_id"] = node.fullName()

        return openpype_data

    def _imprint(self, node: Gaffer.Node, data: dict):
        # Instance id is the node's unique full name so we don't need to
        # imprint as data. This makes it so that duplicating a node will
        # correctly detect it as a new unique instance.
        data.pop("instance_id", None)

        # Prefix all keys
        openpype_data = {}
        for key, value in data.items():
            key = f"{self.attr_prefix}{key}"
            openpype_data[key] = value

        imprint(node, openpype_data)


class GafferCreatorError(CreatorError):
    pass


class GafferCreatorBase(NewCreator, CreatorImprintReadMixin):
    """Base class for single node Creators in Gaffer.

    Child classes must implement `_create_node` to define the node to be
    Created. Aside of that everything should already be handled by the base
    class but can be overridden for special cases.

    """
    default_variants = ["Main"]
    selected_nodes = []

    @abstractmethod
    def _create_node(self,
                     subset_name: str,
                     pre_create_data: dict) -> Gaffer.Node:
        """Create the relevant node type for the instance.

        This only gets called on Create, update is handled automatically by
        updating imprinted data on this node.

        Arguments:
            subset_name (str): The subset name to be created. Usually used for
                the node's name.
            pre_create_data (dict): The `pre_create_data` of the `create` call
                of this Creator.

        Returns:
            Gaffer.Node: The created node.

        """
        pass

    def set_selected_nodes(self, pre_create_data, script):
        if pre_create_data.get("use_selection"):
            self.selected_nodes = script.selection()
            if len(self.selected_nodes) == 0:
                raise GafferCreatorError("Creator error: No nodes selected")

        else:
            self.selected_nodes = []

    def create_nice_label(self, instance_data):
        product_name = instance_data["subset"]
        folder_path = instance_data["folderPath"]
        return f"{product_name} [{folder_path.split('/')[-1]}]"

    def create(self, subset_name, instance_data, pre_create_data):
        instance_data.update({
            "id": "pyblish.avalon.instance",
            "subset": subset_name
        })

        script = get_root()
        assert script, "Must have a gaffer scene script as root"

        # populate self.selecte_nodes
        self.set_selected_nodes(pre_create_data, script)

        # Create a box node for publishing
        node = self._create_node(subset_name, pre_create_data, script)

        # Register the CreatedInstance
        instance = CreatedInstance(
            family=self.family,
            subset_name=subset_name,
            data=instance_data,
            creator=self,
        )
        data = instance.data_to_store()
        self._imprint(node, data)

        # Insert the transient data
        instance.transient_data["node"] = node
        new_label = self.create_nice_label(instance.data)
        instance.data["label"] = new_label

        node.setName(f"{subset_name}_{instance.data['folderPath'].split('/')[-1]}")

        self._add_instance_to_context(instance)

        return instance

    def collect_instances(self):

        script = get_root()
        assert script, "Must have a gaffer scene script as root"
        for node in script.children(Gaffer.Node):
            data = self._read(node)
            if data.get("creator_identifier") != self.identifier:
                continue

            # Add instance
            created_instance = CreatedInstance.from_existing(data, self)

            # Collect transient data
            created_instance.transient_data["node"] = node
            new_label = self.create_nice_label(created_instance.data)
            created_instance.data["label"] = new_label
            #new_label = f"{product_name} [{folder_path.split('/')[-1]}]"
            #instance.data["label"] = new_label

            self._add_instance_to_context(created_instance)

    def update_instances(self, update_list):
        for created_inst, _changes in update_list:
            new_data = created_inst.data_to_store()
            box = created_inst.transient_data["node"]
            self._imprint(box, new_data)

    def remove_instances(self, instances):
        for instance in instances:
            # Remove the tool from the scene

            node = instance.transient_data["node"]
            if node:
                parent = node.parent()
                parent.removeChild(node)
                del node

            # Remove the collected CreatedInstance to remove from UI directly
            self._remove_instance_from_context(instance)

    def get_pre_create_attr_defs(self):
        return [
            BoolDef(
                "use_selection",
                default=False,
                label="Use selection"
            )
        ]


class GafferRenderCreator(NewCreator, CreatorImprintReadMixin):
    """Creator which creates an instance per renderlayer upstream from each
    publish job nodes

    Child classes must implement `_create_node` to define the node to be
    Created. Aside of that everything should already be handled by the base
    class but can be overridden for special cases.

    """
    default_variants = ["Main"]
    selected_nodes = []

    @abstractmethod
    def _create_node(self,
                     subset_name: str,
                     pre_create_data: dict) -> Gaffer.Node:
        """Create the relevant node type for the instance.

        This only gets called on Create, update is handled automatically by
        updating imprinted data on this node.

        Arguments:
            subset_name (str): The subset name to be created. Usually used for
                the node's name.
            pre_create_data (dict): The `pre_create_data` of the `create` call
                of this Creator.

        Returns:
            Gaffer.Node: The created node.

        """
        pass

    def create(self, subset_name, instance_data, pre_create_data):
        self.log.info('create()')
        instance_data.update({
            "id": "pyblish.avalon.instance",
            "subset": subset_name
        })

        script = get_root()
        assert script, "Must have a gaffer scene script as root"

        # Create a box node for publishing
        node = self._create_node(subset_name, pre_create_data, script)

        # add an annotation to highlight where this is publishing to
        Gaffer.Metadata.registerValue(
            node,
            "annotation:user:text",
            instance_data["folderPath"]
        )
        Gaffer.Metadata.registerValue(
            node,
            "annotation:user:color",
            imath.Color3f(0.150000006, 0.25999999, 0.25999999)
        )
        # Register the CreatedInstance
        instance = CreatedInstance(
            family=self.family,
            subset_name=subset_name,
            data=instance_data,
            creator=self,
        )
        data = instance.data_to_store()
        self._imprint(node, data)

        # Insert the transient data
        instance.transient_data["node"] = node

        # self._add_instance_to_context(instance)

        # return instance
        self.collect_instances()

    def collect_instances(self):
        self.log.info('Collecting instances!')
        script = get_root()
        assert script, "Must have a gaffer scene script as root"
        for publish_node in script.children(AyonPublishTask):
            data = self._read(publish_node)
            if data.get("creator_identifier") != self.identifier:
                self.log.debug(f'Skipping {publish_node}, wrong creator id')
                continue

            layers = Gaffer.NodeAlgo.upstreamNodes(
                publish_node,
                RenderLayerNode
            )

            for layer in layers:
                layer_name = layer['layer_name'].getValue()

                project_name = self.create_context.get_current_project_name()
                asset_name = data["folderPath"]
                instance_data = {
                    "task": data["task"],
                    "variant": layer_name,
                }
                if AYON_SERVER_ENABLED:
                    instance_data["folderPath"] = asset_name
                else:
                    instance_data["asset"] = asset_name
                asset_doc = get_asset_by_name(project_name, asset_name)
                subset_name = self.get_subset_name(
                    layer_name,
                    instance_data["task"],
                    asset_doc,
                    project_name)

                instance = CreatedInstance(
                    family=self.family,
                    subset_name=subset_name,
                    data=instance_data,
                    creator=self
                )
                instance.transient_data["node"] = layer
                instance.transient_data["parent_publish_node"] = publish_node
                new_label = f"{subset_name} [{asset_name.split('/')[-1]}]"
                instance.data["label"] = new_label
                self._add_instance_to_context(instance)

    def update_instances(self, update_list):
        for instance, _changes in update_list:
            the_node = instance.transient_data["node"]
            new_data = instance.data_to_store()
            self._imprint(the_node, new_data)

    def remove_instances(self, instances):
        pub_nodes_to_remove = []
        for instance in instances:
            # Remove the tool from the scene

            node = instance.transient_data["parent_publish_node"]
            pub_nodes_to_remove.append(node)

        for instance in list(self.create_context.instances):
            if instance.get('creator_identifier') == self.identifier:
                pub_node = instance.transient_data["parent_publish_node"]
                if pub_node in pub_nodes_to_remove:
                    self._remove_instance_from_context(instance)

        for pub_node in pub_nodes_to_remove:
            parent = node.parent()
            parent.removeChild(node)
            del node
