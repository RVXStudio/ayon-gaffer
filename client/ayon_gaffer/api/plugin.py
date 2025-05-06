import json
import imath
import qargparse
from abc import abstractmethod

from ayon_core.pipeline import (
    Creator as NewCreator,
    CreatedInstance,
    CreatorError,
    load, publish,
)

from ayon_core.lib import (
    BoolDef
)
import ayon_api

from ayon_gaffer.api import (
    get_root,
    imprint_container,
)
from ayon_gaffer.api.pipeline import (
    imprint,
    JSON_PREFIX
)
from ayon_core.pipeline import AYON_INSTANCE_ID
from ayon_core.lib import filter_profiles

import ayon_gaffer.api.lib

from ayon_gaffer.api.nodes import (
    AyonPublishTask,
    RenderLayerNode,
)
from ayon_gaffer.api.pipeline import AYON_ATTR_GROUP_KEY

import Gaffer
import imath

from ayon_core.lib import Logger

log = Logger.get_logger("ayon_gaffer.api.plugin")


def read(node):
    """Read all 'user' custom data on the node"""
    if "user" not in node:
        # No user attributes
        return {}

    data = {}
    if "ayon_attr_group" in node["user"]:
        data["_attr_groups_"] = True
        # we have some groups
        root_plug = node["user"]["ayon_attr_group"]
        for child in root_plug.children():
            group = child["name"].getValue()
            group_data = {}
            for key in child["value"].children():
                group_data[key["name"].getValue()] = key["value"].getValue()
            data[group] = group_data
    for plug in node["user"]:
        plug_name = plug.getName()
        if plug_name == "ayon_attr_group":
            continue
        data[plug_name] = plug.getValue()
    return data


class CreatorImprintReadMixin:
    """Mixin providing _read and _imprint methods to be used by Creators."""

    attr_prefix = "ayon_"
    op_attr_prefix = "openpype_"

    def _read(self, node: Gaffer.Node) -> dict:
        all_user_data = read(node)

        # Consider only data with the special attribute prefix
        # and strip off the prefix as for the resulting data

        def read_data_dict(in_data, node):
            ayon_data = {}
            for key, value in in_data.items():

                if key.startswith(self.attr_prefix):
                    prefix_len = len(self.attr_prefix)
                elif key.startswith(self.op_attr_prefix):
                    prefix_len = len(self.op_attr_prefix)
                else:
                    continue

                if isinstance(value, str) and value.startswith(JSON_PREFIX):
                    value = value[len(JSON_PREFIX):]  # strip off JSON prefix
                    value = json.loads(value)
                elif isinstance(value, str) and value == "<None>":
                    value = None

                key = key[prefix_len:]      # strip off prefix
                ayon_data[key] = value

            ayon_data["instance_id"] = node.fullName()
            if "creator_identifier" in ayon_data.keys():
                # if we have an openpye creator identifier, let's temporarily
                # make it an ayon one.
                creator_id = ayon_data["creator_identifier"]
                if ".openpype." in creator_id:
                    ayon_data["creator_identifier"] = creator_id.replace(
                        ".openpype.", ".ayon.")
            return ayon_data

        if all_user_data.get("_attr_groups_"):
            # we have groups
            ayon_data = {}
            for k, v in all_user_data.items():
                if k == "_attr_groups_":
                    continue
                if not isinstance(v, dict):
                    continue
                ayon_data[k] = read_data_dict(v, node)

            ayon_data["_attr_groups_"] = True

        else:
            ayon_data = read_data_dict(all_user_data, node)

        return ayon_data

    def _imprint(self, node: Gaffer.Node, data: dict):
        # Instance id is the node's unique full name so we don't need to
        # imprint as data. This makes it so that duplicating a node will
        # correctly detect it as a new unique instance.
        data.pop("instance_id", None)

        # Prefix all keys
        ayon_data = {}
        for key, value in data.items():
            key = f"{self.attr_prefix}{key}"
            ayon_data[key] = value

        imprint(node, ayon_data)

    def _layer_imprint(
        self, node: Gaffer.Node, data: dict, publish_node: Gaffer.Node
            ):
        # print("% LAYER Imprinting", node.getName())
        # Instance id is the node's unique full name so we don't need to
        # imprint as data. This makes it so that duplicating a node will
        # correctly detect it as a new unique instance.
        data.pop("instance_id", None)

        # Prefix all keys
        ayon_data = {}
        for key, value in data.items():
            key = f"{self.attr_prefix}{key}"
            ayon_data[key] = value

        imprint(node, ayon_data, group=publish_node.fullName())


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
                     product_name: str,
                     pre_create_data: dict) -> Gaffer.Node:
        """Create the relevant node type for the instance.

        This only gets called on Create, update is handled automatically by
        updating imprinted data on this node.

        Arguments:
            product_name (str): The product name to be created. Usually used for
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
        product_name = instance_data["productName"]

        folder_path = instance_data["folderPath"]
        return f"{product_name} [{folder_path}]"

    def create(self, product_name, instance_data, pre_create_data):
        instance_data.update({
            "id": AYON_INSTANCE_ID,
            "productName": product_name
        })

        # strip out the task
        instance_data["task"] = None

        script = get_root()
        assert script, "Must have a gaffer scene script as root"

        # populate self.selecte_nodes
        self.set_selected_nodes(pre_create_data, script)

        # Create a box node for publishing
        node = self._create_node(product_name, pre_create_data, script)

        # Register the CreatedInstance
        instance = CreatedInstance(
            product_type=self.product_type,
            product_name=product_name,
            data=instance_data,
            creator=self,
        )
        data = instance.data_to_store()

        self._imprint(node, data)

        # Insert the transient data
        instance.transient_data["node"] = node
        new_label = self.create_nice_label(instance.data)
        instance.data["label"] = new_label

        node.setName(
            f"{product_name}_{instance.data['folderPath'].split('/')[-1]}")

        self._add_instance_to_context(instance)

        return instance

    def collect_instances(self):

        script = get_root()
        assert script, "Must have a gaffer scene script as root"
        if hasattr(self, "deprecated_identifiers"):
            identifiers = [self.identifier] + self.deprecated_identifiers
        else:
            identifiers = [self.identifier]
        for node in script.children(Gaffer.Node):
            data = self._read(node)
            if data.get("creator_identifier") not in identifiers:
                continue

            # TODO: I need to understand better how tasks work after the
            # ayon_core move
            # if there is not task, we need it to be None, instead of ""
            task = data.get("task")
            if task is not None and task == "":
                data["task"] = None
            # Add instance
            created_instance = CreatedInstance.from_existing(data, self)

            # Collect transient data
            created_instance.transient_data["node"] = node
            new_label = self.create_nice_label(created_instance.data)
            created_instance.data["label"] = new_label
            # new_label = f"{product_name} [{folder_path.split('/')[-1]}]"
            # instance.data["label"] = new_label

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
                     product_name: str,
                     pre_create_data: dict) -> Gaffer.Node:
        """Create the relevant node type for the instance.

        This only gets called on Create, update is handled automatically by
        updating imprinted data on this node.

        Arguments:
            product_name (str): The product name to be created. Usually used
                for the node's name.
            pre_create_data (dict): The `pre_create_data` of the `create` call
                of this Creator.

        Returns:
            Gaffer.Node: The created node.

        """
        pass

    def create(self, product_name, instance_data, pre_create_data):
        self.log.info('create()')
        instance_data.update({
            "id": AYON_INSTANCE_ID,
            "productName": product_name
        })

        script = get_root()
        assert script, "Must have a gaffer scene script as root"

        # Create a box node for publishing
        node = self._create_node(product_name, pre_create_data, script)

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
            product_type=self.product_type,
            product_name=product_name,
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

        if hasattr(self, "deprecated_identifiers"):
            identifiers = [self.identifier] + self.deprecated_identifiers
        else:
            identifiers = [self.identifier]
        for publish_node in script.children(AyonPublishTask):
            data = self._read(publish_node)
            if data.get("creator_identifier") not in identifiers:
                self.log.info("{} - {}".format(
                    data.get("creator_identifier"), self.identifier))
                self.log.debug(f'Skipping {publish_node}, wrong creator id')
                continue

            layers = Gaffer.NodeAlgo.upstreamNodes(
                publish_node,
                RenderLayerNode
            )

            for layer in layers:
                layer_name = layer['layer_name'].getValue().strip()

                project_name = self.create_context.get_current_project_name()
                layer_data = self._read(layer)
                if layer_data.get("_attr_groups_"):
                    layer_data = layer_data.get(publish_node.fullName(), {})
                if layer_data.get("folderPath") is None:
                    # we need to create the instance data for this layer

                    folder_path = data["folderPath"]
                    instance_data = {
                        "task": data["task"],
                        "variant": layer_name,
                    }
                    instance_data["folderPath"] = folder_path
                    folder = ayon_api.get_folder_by_path(
                        project_name, folder_path)
                    task_entity = ayon_api.get_task_by_name(
                        project_name, folder["id"], instance_data["task"]
                    )
                    product_name = self.get_product_name(
                        project_name,
                        folder,
                        task_entity,
                        layer_name,
                        )

                    if "layer" in layer_data.keys():
                        del layer_data["label"]
                    if "productName" in layer_data.keys():
                        del layer_data["productName"]
                    if "instance_id" in layer_data.keys():
                        del layer_data["instance_id"]
                    instance_data.update(layer_data)
                    instance = CreatedInstance(
                        product_type=self.product_type,
                        product_name=product_name,
                        data=instance_data,
                        creator=self
                    )
                else:
                    instance = CreatedInstance.from_existing(layer_data, self)
                    # we want the folder path from the publish node, that the
                    # renderlayer is connected into
                    folder_path = data["folderPath"]
                    folder = ayon_api.get_folder_by_path(
                        project_name, folder_path)
                    task_entity = ayon_api.get_task_by_name(
                        project_name, folder["id"], layer_data["task"],)
                    product_name = self.get_product_name(
                        project_name,
                        folder,
                        task_entity,
                        layer_name,
                    )
                    instance.data["variant"] = layer_name
                instance.transient_data["node"] = layer
                instance.transient_data["parent_publish_node"] = publish_node

                new_label = f"{product_name} [{folder_path}]"

                instance.data["label"] = new_label
                self._add_instance_to_context(instance)
        self.clean_render_layer_imprints()

    def update_instances(self, update_list):
        for instance, _changes in update_list:
            # we imprint the layer nodes, not the publish nodes,
            the_node = instance.transient_data["node"]
            publish_node = instance.transient_data["parent_publish_node"]
            new_data = instance.data_to_store()

            # we remove some data, since that is set on the publish node
            # and it makes no sense to be able to change one shot for all
            # layers
            publish_node_data = {}
            for key in ["folderPath", "task"]:
                publish_node_data[key] = new_data[key]
                del new_data[key]

            self._layer_imprint(the_node, new_data, publish_node)

            self._imprint(publish_node, publish_node_data)
            Gaffer.Metadata.registerValue(
                publish_node,
                "annotation:user:text",
                publish_node_data["folderPath"]
            )
        self.clean_render_layer_imprints()

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

    def clean_render_layer_imprints(self):
        log.info("CLEANING IMPRINT")
        nodes_to_check = []
        for instance in list(self.create_context.instances):
            if instance.get('creator_identifier') == self.identifier:
                instance_node = instance.transient_data['node']
                if instance_node not in nodes_to_check:
                    nodes_to_check.append(instance_node)

        for inode in nodes_to_check:
            to_delete = []
            output_plugs = inode["out_render"].outputs()
            outputs = [f.node().fullName() for f in output_plugs]
            for child in inode["user"][AYON_ATTR_GROUP_KEY].children():
                group_name = child["name"].getValue()
                if group_name not in outputs:
                    log.info(f"Cleaning out group [{group_name}]")
                    to_delete.append(child)

            for item in to_delete:
                inode["user"][AYON_ATTR_GROUP_KEY].removeChild(item)


class PlugSettingsMixin:
    def apply_plug_settings(self, node):
        # print("Applygin plug from settings")
        for plug in self.plugs:
            plug_name = plug["name"]
            plug_type = plug["type"]
            plug_value = plug[plug_type]

            # print(f"* {plug_name}")

            # now let's find the actual plug
            plug_path = plug_name.split(".")
            try:
                target_plug = node
                for pp in plug_path:
                    target_plug = target_plug[pp]
            except KeyError:
                log.debug(f"No plug [{plug_path}] for node {node}")
                continue

            if plug_type in ["text", "boolean", "number", "decimal"]:
                log.debug(f"Setting [{target_plug}] to [{plug_value}]")
                pass  # we just pass plug_value on as-is

            elif plug_type == "v2f":
                plug_value = imath.V2f(plug_value["x"], plug_value["y"])
            elif plug_type == "v3f":
                plug_value = imath.V2f(
                        plug_value["x"], plug_value["y"], plug_value["z"])
            elif plug_type == "color3f":
                plug_value = imath.Color3f(
                        plug_value["r"], plug_value["g"], plug_value["b"])
            elif plug_type == "color4f":
                plug_value = imath.Color4f(
                        plug_value["r"],
                        plug_value["g"],
                        plug_value["b"],
                        plug_value["a"])
            try:
                target_plug.setValue(plug_value)
            except Exception as err:
                log.error(f"ERROR: {err}")


class GafferLoaderBase(load.LoaderPlugin):
    def set_node_color(self, node, context):
        product_type = context["product"].get("productType", "")
        ayon_gaffer.api.lib.set_node_color_from_settings(node, product_type)

    def add_node_to_graph(self, node):
        """
        Add the given node to the newest visible graph editor, if there is no
        visible graph editor use the newest hidden; if there is no grapheditor
        whatsoever just add it to the scriptroot
        """
        import GafferUI
        script = get_root()
        sw = GafferUI.ScriptWindow.acquire(script)

        layout = sw.getLayout()
        graphEditors = [e for e in layout.editors() if isinstance(
            e, GafferUI.GraphEditor)]
        visibleGraphEditors = [e for e in graphEditors if e.visible()]

        if len(visibleGraphEditors) == 0:
            if len(graphEditors) == 0:
                graph_editor = None
            else:
                # use all
                graph_editor = graphEditors[0]
        else:
            graph_editor = visibleGraphEditors[0]

        if graph_editor is None:
            viewedNode = script
        else:
            viewedNode = graph_editor.graphGadget().getRoot()
        viewedNode.addChild(node)


class GafferExtractorPlugin(publish.Extractor):
    """Base class for extract plugins."""
    settings_category = "gaffer"
    hosts = ["gaffer"]


class GafferImageLoaderBase(GafferLoaderBase, PlugSettingsMixin):

    node_name_template = None  # will be populated by settings
    use_udims = False

    @classmethod
    def get_options(cls, *args):
        return [
            qargparse.Enum(
                "udim_mode",
                label="UDIMs?",
                help=("When loading sequences, by default udims are used for"
                      " certain productType/productName profiles, this allows"
                      " to override that behaviour"),
                items=["<use settings>", "Load with UDIMs", "No UDIMs"],
                default=0
            )
        ]

    @classmethod
    def apply_settings(cls, project_settings):
        super(GafferImageLoaderBase, cls).apply_settings(project_settings)

        try:
            # check if we can import GafferArnold -> is Arnold loaded?
            import GafferArnold  # noqa
        except ModuleNotFoundError:
            # if not we just disable this loader quietly
            print("GafferArnold not available; disable GafferLoadImageAiImage")
            cls.enabled = False

    def set_up_node(self, name, namespace, node, context):
        '''
        Set up the node - add it to the script node, set it's name and color
        and apply plug settings
        '''
        node.setName(self._get_node_name(context))

        self.add_node_to_graph(node)
        self.set_node_color(node, context)

        self.apply_plug_settings(node)

        imprint_container(node,
                          name=name,
                          namespace=namespace,
                          context=context,
                          loader=self.__class__.__name__)

        # store the use_udims value on the node so we can use it when we update
        # the node
        imprint(node, {"use_udims": self.use_udims})

    def _get_node_name(self, context):
        return ayon_gaffer.api.lib.node_name_from_template(
            self.node_name_template, context)

    def prepare_image_path(self, context, options=None, node=None):
        """
        Since the paths from the representations are just the first frame
        we need to check if this is a sequence we are loading and if so
        we need to format it with hash padding for gaffer.

        However if UDIM loading is set to true (profiles in settings or
        override in options) we don't use padding, but use "<UDIM>"instead.
        """
        path = self.filepath_from_context(context)
        # first check the options
        if options is None:
            # we don't have any options, so this is coming from an update!
            if node is None:
                raise RuntimeError(f"No node given and no options! What should"
                                   " I do with that?")

            if "use_udims" in node["user"]:
                self.use_udims = node["user"]["use_udims"].getValue()
            else:
                self.log.warning(f"I can't find 'use_udims' on the node, "
                                 "assuming False")
                self.use_udims = False
        else:
            # the options are a dictionary, so we are loading!
            udim_mode = options.get("udim_mode", "<use settings>")
            self.log.warning(f"um: {udim_mode}")
            if udim_mode == "<use settings>":
                product_type = context["product"]["productType"]
                product_name = context["product"]["name"]
                selected_profile = filter_profiles(
                    self.udim_profiles,
                    {
                        'product_type': product_type,
                        'product_name': product_name
                    },
                )
                if selected_profile is None:
                    # no profile
                    self.use_udims = False
                else:
                    self.use_udims = selected_profile["use_udims"]
            elif udim_mode == "Load with UDIMs":
                self.use_udims = True
            elif udim_mode == "No UDIMs":
                self.use_udims = False
            else:
                raise RuntimeError(
                    f"Encoutered a weird udim mode: [{udim_mode}]")
        self.log.info(f"use_udims: {self.use_udims}")

        seq = ayon_gaffer.api.utils.get_pyseq_sequence(path)
        if len(seq) > 1:
            padding = seq._get_padding()
            hash_padding = int(padding[1:-1])*"#"  # convert %04d to ####
            if self.use_udims:
                self.log.info("Sequence, replacing padding with '<UDIM>'")
                out_path = "{}<UDIM>{}".format(
                    seq.format(f"%D%h"), seq.format("%t"))
            else:
                self.log.info("Sequence, replacing padding with '#'")
                out_path = seq.format(f"%D%h{hash_padding}%t")
        else:
            out_path = seq.path()
        return out_path.replace("\\", "/")

    def remove(self, container):
        node = container["_node"]

        parent = node.parent()
        parent.removeChild(node)

    def switch(self, container, context):
        self.update(container, context)

    def set_node_colorspace(self, colorspace_plug, context, filepath):
        from GafferImageUI import OpenColorIOTransformUI
        # import GafferUI

        project_name = context["project"]["name"]
        representation = context["representation"]

        colorspace = (ayon_gaffer.api.
                      colorspace.get_representation_colorspace_data(
                        project_name, representation, filepath
                      ))

        if colorspace:
            # check if the selected colorspace exists!
            available = OpenColorIOTransformUI.colorSpacePresetValues(
                    colorspace_plug)
            if colorspace not in available:
                error = (f"Colorspace [{colorspace}] does not exist on plug "
                         f"[{colorspace_plug.node().getName()}."
                         f"{colorspace_plug.getName()}]")
                self.log.error(error)
                # dlg = GafferUI.ErrorDialogue(
                #     "Load image error",
                #     error)
                # dlg.waitForButton()
                # dlg.close()
                return
            self.log.info(f"Setting colorspace to {colorspace}")
            colorspace_plug.setValue(colorspace)
            ayon_gaffer.api.pipeline.imprint(
                colorspace_plug.node(),
                {"db_colorspace": colorspace})
        else:
            self.log.warning(
                f"No colorspace for {colorspace_plug.node().getName()}")
