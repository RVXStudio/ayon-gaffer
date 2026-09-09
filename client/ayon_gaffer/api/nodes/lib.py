import os
from functools import partial
import re
import Gaffer
import imath

import IECore

from ayon_core.lib import Logger
from ayon_gaffer.api import lib
import ayon_gaffer.api.pipeline

log = Logger.get_logger(__name__)

BOXNODE_TYPE_PLUG_NAME = "boxnode_type"
BOXNODE_VERSION_PLUG_NAME = "boxnode_version"
BOXNODE_MENU_PREFIX = "/AYON/boxnodes"

BoxNodeManagerInstance = None


class BoxNodeManager():
    """
    A class to handle registering, and versioning boxnodes.

    For now instanced only once when register_boxnode_path is called. Most of
    it's functionality is exposed in methods in this module
    """
    _paths = []
    _nodetree = {}

    @classmethod
    def register_path(cls, in_path):
        """
        Add a path to the manager; it will then refresh.
        """
        if in_path not in cls._paths:
            cls._paths.append(in_path)
        else:
            log.debug(f"skipping [{in_path}]")
        cls.refresh()

    @classmethod
    def list(cls):
        return cls._nodetree

    @classmethod
    def refresh(cls):
        """
        Traverse registered paths and find .gfr files that follow a certain
        pattern:

          {registered_path}/{node_type}/{node_type}_{version}.gfr

        this is then used to populate the version tree for the manager.
        """

        cls._nodetree = {}
        for path in cls._paths:
            try:
                node_types = os.listdir(path)
            except (PermissionError, FileNotFoundError) as err:
                # we can't read this folder
                log.error(err)
                return
            for node_type in node_types:
                node_type_path = os.path.join(path, node_type)
                if not os.path.isdir(node_type_path):
                    continue
                node_versions = {}
                version_expression = re.compile(node_type + r"_v?(.+)\.gfr")
                for version_file in os.listdir(node_type_path):
                    match = re.match(version_expression, version_file)
                    if match is None:
                        log.debug(f"File [{version_file}] does not match"
                                  f"expression [{version_expression}]")
                        continue
                    version = match.group(1)
                    node_file = os.path.join(
                        node_type_path,
                        f"{version_file}"
                    )
                    if os.path.exists(node_file):
                        node_versions[version] = node_file
                cls._nodetree[node_type] = node_versions

    @classmethod
    def find_node_path(cls, node_type, node_version):
        """
        Get a path to the gfr file for the given `node_type` of the
        `node_version`
        """

        node_info = cls.list().get(node_type)
        if node_info is None:
            raise RuntimeError(f"Node of type [{node_type}] not found!")

        node_file_path = node_info.get(node_version)
        if node_file_path is None:
            raise RuntimeError(f"Version [{node_version}] does "
                               "not exist for type [{node_type}]")
        return node_file_path

    @classmethod
    def update(cls, nodes, new_version=None):
        """
        Update given Gaffer.Node objects `nodes` to the specified `new_version`
        if `new_version` is None it will update to the latest registered
        version of the given `nodes`
        """
        if not (isinstance(nodes, (list, tuple))
                or isinstance(nodes, Gaffer.StandardSet)):
            nodes = [nodes]

        replacements = []
        for node in nodes:
            if BOXNODE_VERSION_PLUG_NAME not in node.keys():
                log.info(f"Node {node} is not a proper boxnode, it's missing"
                         f"the {BOXNODE_VERSION_PLUG_NAME} plug")
                continue

            # for node in nodes:
            node_type = get_boxnode_type(node)
            old_version = node[BOXNODE_VERSION_PLUG_NAME].getValue()
            try:
                latest_version = cls.get_versions_for_node_type(node_type)[0]

                if new_version is None:
                    input_version = latest_version
                else:
                    input_version = new_version
                if input_version == old_version:
                    continue
                new_node = cls.create(
                    node.scriptNode(), node_type, new_version)
                replacements.append((node, new_node))
            except RuntimeError as err:
                log.error(f"Error updating: {err}")
                continue

        for old_node, new_node in replacements:
            lib.replace_node(
                old_node,
                new_node,
                ignore_plug_names=[BOXNODE_VERSION_PLUG_NAME]
            )

    @classmethod
    def create(cls, script_node, node_type, node_version):
        """
        Create a node in the given script.
        """
        import GafferUI

        if node_version is None:
            versions = cls.get_versions_for_node_type(node_type)
            if len(versions) == 0:
                log.error(f"No versions found for [{node_type}]")
                return []
            node_version = versions[0]

        node_file_path = cls.find_node_path(node_type, node_version)
        log.info(f"Creating [{node_type}] from {node_file_path}")

        with Gaffer.UndoScope(script_node):
            script_inventory = set(script_node.children())
            script_node.importFile(node_file_path)
            post_inventory = set(script_node.children())
            added_nodes = list(post_inventory - script_inventory)

        for anode in added_nodes:
            add_boxnode_plugs(anode, node_type, node_version)
        # position the node
        graph_editor = GafferUI.GraphEditor.acquire(script_node)
        bound = graph_editor.bound()
        graph_gadget = graph_editor.graphGadget()
        graph_vgadget = graph_editor.graphGadgetWidget().getViewportGadget()

        mousePosition = GafferUI.Widget.mousePosition()
        if bound.intersects(mousePosition):
            fallbackPosition = mousePosition - bound.min()
        else:
            fallbackPosition = bound.center() - bound.min()
        fallbackPosition = graph_vgadget.rasterToGadgetSpace(
            imath.V2f(fallbackPosition.x, fallbackPosition.y),
            gadget=graph_gadget
        ).p0
        fallbackPosition = imath.V2f(fallbackPosition.x, fallbackPosition.y)
        graph_gadget.getLayout().positionNodes(
            graph_editor.graphGadget(),
            Gaffer.StandardSet(added_nodes),
            fallbackPosition
        )
        default_icon = Gaffer.Metadata.value(added_nodes[0], "defaulticon")
        if default_icon is not None:
            Gaffer.Metadata.registerValue(
                added_nodes[0], 'icon', default_icon)
        return added_nodes[0]

    @classmethod
    def check_versions(cls, script_node):
        """
        Will iterate over the nodes in the `script_node` and check if
        theirs is the latest version.
        """
        node_tree = cls.list()
        node_types = list(node_tree.keys())
        to_update_count = 0
        ok_count = 0
        for box_node in script_node.children(Gaffer.Box):
            node_type = get_boxnode_type(box_node)
            if BOXNODE_VERSION_PLUG_NAME not in box_node.keys():
                log.debug(f"[{box_node}] does not have version plug. Skipping")
                continue
            current_version = box_node[BOXNODE_VERSION_PLUG_NAME].getValue()
            if node_type in node_types:
                existing_versions = sorted(
                    list(node_tree[node_type].keys()), reverse=True)
                if (current_version not in existing_versions or
                        existing_versions.index(current_version) != 0):
                    Gaffer.Metadata.registerValue(
                        box_node, "icon", "rocking-chair.png")
                    to_update_count += 1
                else:
                    default_icon = Gaffer.Metadata.value(
                        box_node, "defaulticon")
                    icon_name = default_icon or "boxNode.png"
                    Gaffer.Metadata.registerValue(
                        box_node, 'icon', icon_name)
                    ok_count += 1
        return (to_update_count, ok_count)

    @classmethod
    def get_versions_for_node_type(cls, node_type):
        node_tree = cls.list()
        if node_type not in node_tree:
            raise RuntimeError(f"Boxnode type [{node_type}] not registered")
        # let's try and make the keys into integes
        keylist = list(node_tree[node_type].keys())
        try:
            sorted_keys = [int(k) for k in keylist]
            sorted_keys.sort(reverse=True)
            # and back to str
            sorted_keys = [str(k) for k in sorted_keys]
        except ValueError:
            # ok, we just bail here
            sorted_keys = sorted(keylist, reverse=True)

        return sorted_keys


def get_boxnode_type(box_node):
    """
    The old way to get the boxnode type was just to inspect the typeName,
    however we can handle boxnodes that are just that, boxes. So their type
    will always be `Gaffer::Box` so to get a custom boxnode type, we add the
    boxnode_type plug. This fetches the new way (the plug) or if that is not
    on the node, just return the old nodeType way.
    """
    if BOXNODE_TYPE_PLUG_NAME in box_node.keys():
        return box_node[BOXNODE_TYPE_PLUG_NAME].getValue()
    else:
        log.debug(f"Falling back to typeName splitting for type")
        return box_node.typeName().split("::")[-1]


def get_boxnode_version(box_node):
    """
    Return the current value of the boxnode version plug, with the v stripped.
    Returns None if no version plug is on the node.
    """
    if BOXNODE_VERSION_PLUG_NAME in box_node.keys():
        return box_node[BOXNODE_VERSION_PLUG_NAME].getValue().strip("v")
    else:
        return None


def add_boxnode_plugs(node, node_type, node_version):
    """
    Add the boxnode metadata plugs and set their value, you'll need to prefix
    `v` to the version to get set proper.

    """
    node.addChild(Gaffer.StringPlug(
        BOXNODE_VERSION_PLUG_NAME,
        flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
        defaultValue="")
    )
    node.addChild(Gaffer.StringPlug(
        BOXNODE_TYPE_PLUG_NAME,
        flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
        defaultValue="")
    )
    node[BOXNODE_VERSION_PLUG_NAME].setValue(node_version or "")
    node[BOXNODE_TYPE_PLUG_NAME].setValue(node_type or "")

    Gaffer.Metadata.registerValue(
        node[BOXNODE_VERSION_PLUG_NAME], 'layout:section', 'Node')
    Gaffer.Metadata.registerValue(
        node[BOXNODE_VERSION_PLUG_NAME], 'nodule:type', '')
    Gaffer.Metadata.registerValue(
        node[BOXNODE_TYPE_PLUG_NAME], 'layout:section', 'Node')
    Gaffer.Metadata.registerValue(
        node[BOXNODE_TYPE_PLUG_NAME], 'nodule:type', '')


def register_boxnode_path(path):
    global BoxNodeManagerInstance
    if BoxNodeManagerInstance is None:
        BoxNodeManagerInstance = BoxNodeManager()

    BoxNodeManagerInstance.register_path(path)


def registered_boxnodes():
    global BoxNodeManagerInstance
    if BoxNodeManagerInstance is None:
        return {}
    return BoxNodeManagerInstance.list()


def create_boxnode(node_type, node_version=None, menu=None, script_node=None):
    import GafferUI
    global BoxNodeManagerInstance
    if BoxNodeManagerInstance is None:
        raise RuntimeError(
            "Could not create boxnode, type manager does not exist!")

    if menu is not None:
        scriptWindow = menu.ancestor(GafferUI.ScriptWindow)
        script_node = scriptWindow.scriptNode()

    new_node = BoxNodeManagerInstance.create(
        script_node, node_type, node_version)
    return new_node


def update_boxnode_menu(application):
    """
    Populates gaffers node menu (the tab menu) with some actions and
    the nodes from the registered paths.
    """

    import GafferUI
    nodeMenu = GafferUI.NodeMenu.acquire(application)

    nodeMenu.definition().removeMatching(f"{BOXNODE_MENU_PREFIX}/.*")

    item = IECore.MenuItemDefinition(
        command=check_boxnode_versions
    )
    menu_path = f"{BOXNODE_MENU_PREFIX}/[a] Check boxnode versions"
    nodeMenu.definition().append(menu_path, item)

    item = IECore.MenuItemDefinition(
        command=update_selected_boxnodes
    )
    menu_path = f"{BOXNODE_MENU_PREFIX}/[a] Update selected boxnodes to latest"
    nodeMenu.definition().append(menu_path, item)

    item = IECore.MenuItemDefinition(
        divider=True
    )
    menu_path = f"{BOXNODE_MENU_PREFIX}/div"
    nodeMenu.definition().append(menu_path, item)

    boxnodes_dict = registered_boxnodes()
    for node_type, node_version_info in boxnodes_dict.items():
        menu_path = f"{BOXNODE_MENU_PREFIX}/{node_type}"
        nodeMenu.append(menu_path, partial(
                create_boxnode,
                node_type
            ))


def check_boxnode_versions(script_node=None, menu=None):
    import GafferUI
    global BoxNodeManagerInstance
    if menu is not None:
        scriptWindow = menu.ancestor(GafferUI.ScriptWindow)
        script_node = scriptWindow.scriptNode()
    if BoxNodeManagerInstance is None:
        raise RuntimeError("BoxNodeManager does not exist!")
    upd, ok = BoxNodeManagerInstance.check_versions(script_node)
    if menu is not None:
        # the user selected to run the action, so we let him know the results
        dlg = GafferUI.ConfirmationDialogue(
            "Boxnode check",
            f"{upd} nodes are out of date, {ok} nodes are at latest")
        dlg.waitForConfirmation()
        dlg.close()


def update_selected_boxnodes(menu=None, script_node=None):
    import GafferUI
    global BoxNodeManagerInstance
    if BoxNodeManagerInstance is None:
        raise RuntimeError(
            "Could not create boxnode, type manager does not exist!")
    if menu is not None:
        scriptWindow = menu.ancestor(GafferUI.ScriptWindow)
        script_node = scriptWindow.scriptNode()
    BoxNodeManagerInstance.update(script_node.selection())


def export_selected_node_as_boxnode(node, graphEditor):
    '''
    This opens a dialog and prompts the user to save the boxnode under a
    certain boxnode path.
    (the ones defined in settings under `node_preset_paths`)
    '''
    from qtpy import QtWidgets
    import GafferUI

    class SaveBoxnodeDialog(QtWidgets.QDialog):
        destination_path = None
        new_version = None

        def __init__(self, parent=None, name="", version=""):
            super(SaveBoxnodeDialog, self).__init__(parent)

            layout = QtWidgets.QFormLayout()
            self.pathBox = QtWidgets.QComboBox()
            self.pathBox.addItems(
                ayon_gaffer.api.pipeline.get_boxnode_paths_from_settings()
            )
            layout.addRow("Boxnode root", self.pathBox)

            self.nameBox = QtWidgets.QLineEdit(name)
            self.versionBox = QtWidgets.QLineEdit(version)

            layout.addRow("Name", self.nameBox)
            layout.addRow("Version", self.versionBox)

            self.previewLabel = QtWidgets.QLabel("")
            layout.addRow(self.previewLabel)

            btnlayout = QtWidgets.QHBoxLayout()
            cancel_btn = QtWidgets.QPushButton('Cancel', self)
            btnlayout.addWidget(cancel_btn)
            self.save_btn = QtWidgets.QPushButton('Save', self)
            btnlayout.addWidget(self.save_btn)
            layout.addRow(btnlayout)
            self.setLayout(layout)

            self.resize(450, 140)
            self.setWindowTitle('Save node as boxnode')
            self.update_destination()

            self.nameBox.textEdited.connect(self.update_destination)
            self.versionBox.textEdited.connect(self.update_destination)
            self.pathBox.currentTextChanged.connect(self.update_destination)

            self.save_btn.clicked.connect(self.accept)
            cancel_btn.clicked.connect(self.reject)

        def update_destination(self):
            base_path = self.pathBox.currentText()
            name = self.nameBox.text().strip()
            version = self.versionBox.text().strip()

            if name == "" or version == "":
                self.previewLabel.setText("< Invalid >")
                self.destination_path = None
                self.save_btn.setEnabled(False)
                self.new_version = None
                return

            filename = f"{name}_v{version}.gfr"

            self.destination_path = os.path.join(base_path, name, filename)

            if os.path.exists(self.destination_path):
                # we won't allow overwriting!
                self.previewLabel.setText(
                    f"!! {self.destination_path} exists!")
                self.save_btn.setEnabled(False)
                self.new_version = None
                return
            self.previewLabel.setText(self.destination_path)
            self.new_version = version
            self.save_btn.setEnabled(True)

    script_node = graphEditor.scriptNode()
    scriptWindow = GafferUI.ScriptWindow.acquire(script_node)

    node_type = get_boxnode_type(node)
    node_version = get_boxnode_version(node) or ""

    # parent the dialog under the main scriptwindow.
    dlg = SaveBoxnodeDialog(scriptWindow._qtWidget(), node_type, node_version)

    res = dlg.exec_()
    if not res:
        return
    # we can save
    destination = dlg.destination_path
    output_dir = os.path.dirname(destination)
    new_version = dlg.new_version
    if not os.path.exists(output_dir):
        log.info(f"Creating boxnode directory [{output_dir}]")
        os.makedirs(output_dir)

    log.info(f"Saving boxnode to [{destination}]")
    export_boxnode(script_node, node, destination, new_version)

    BoxNodeManagerInstance.refresh()
    application = script_node.applicationRoot()
    update_boxnode_menu(application)


def export_boxnode(script_node, node, destination, new_version):
    # we need trim out the boxnode attributes
    node_type = get_boxnode_type(node)
    # node_version = get_boxnode_version(node)

    if BOXNODE_VERSION_PLUG_NAME in node.keys():
        node.removeChild(node[BOXNODE_VERSION_PLUG_NAME])
    if BOXNODE_TYPE_PLUG_NAME in node.keys():
        node.removeChild(node[BOXNODE_TYPE_PLUG_NAME])

    Gaffer.Metadata.registerValue(
        node,
        "noduleLayout:customGadget:addButtonTop:visible",
        False
    )
    Gaffer.Metadata.registerValue(
        node,
        "noduleLayout:customGadget:addButtonBottom:visible",
        False
    )
    Gaffer.Metadata.registerValue(
        node,
        "noduleLayout:customGadget:addButtonLeft:visible",
        False
    )
    Gaffer.Metadata.registerValue(
        node,
        "noduleLayout:customGadget:addButtonRight:visible",
        False
    )

    parent = node.parent()
    sel = script_node.selection()
    old = sel[:]
    sel.clear()
    sel.add(node)
    script_node.serialiseToFile(destination, parent, sel)
    sel.clear()
    for x in old:
        sel.add(x)

    add_boxnode_plugs(node, node_type, f"v{new_version}")
