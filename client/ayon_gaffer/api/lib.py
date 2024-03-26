import sys
from queue import SimpleQueue
from typing import Tuple, List, Optional

import Gaffer
import GafferScene
import imath

if sys.version_info >= (3, 9, 0):
    from collections.abc import Iterator
else:
    from typing import Iterator

from openpype.pipeline import registered_host
from openpype.client import (
    get_asset_by_name
)
from openpype.lib import Logger
import ayon_api

log = Logger.get_logger('openpype.hosts.gaffer.api.lib')


def set_node_color(node: Gaffer.Node, color: Tuple[float, float, float]):
    """Set node color.

    Args:
        node (Gaffer.Node): Node to set the color for.
        color (tuple): 3 float values representing RGB between 0.0-1.0

    Returns:
        None

    """
    assert len(color) == 3, "Color must be three float values"
    Gaffer.Metadata.registerValue(node, "nodeGadget:color",
                                  imath.Color3f(*color))


def make_box(name: str,
             add_input: bool = True,
             add_output: bool = True,
             description: Optional[str] = None,
             hide_add_buttons: bool = True) -> Gaffer.Box:
    """Create a Box node with BoxIn and BoxOut nodes

    Note:
        The box is not added as child anywhere - to have it visually
        appear make sure to call e.g. `parent.addChild(box)`

    Arguments:
        name (str): The name to give the box.
        add_input (bool): Whether to add an input child plug.
        add_output (bool): Whether to add an output child plug.
        description (Optional[str]): A description to register for the box.
        hide_add_buttons (bool): Whether the add buttons on the box
            node should be hidden or not. By default, this will hide them.

    Returns:
        Gaffer.Box: The created box

    """

    box = Gaffer.Box(name)

    if description:
        Gaffer.Metadata.registerValue(box, 'description', description)

    if add_input:
        box_in = Gaffer.BoxIn("BoxIn")
        box.addChild(box_in)
        box_in.setup(GafferScene.ScenePlug("out"))

    if add_output:
        box_out = Gaffer.BoxOut("BoxOut")
        box.addChild(box_out)
        box_out.setup(GafferScene.ScenePlug("in",))

    if hide_add_buttons:
        for key in [
            'noduleLayout:customGadget:addButtonTop:visible',
            'noduleLayout:customGadget:addButtonBottom:visible',
            'noduleLayout:customGadget:addButtonLeft:visible',
            'noduleLayout:customGadget:addButtonRight:visible',
        ]:
            Gaffer.Metadata.registerValue(box, key, False)

    return box


def arrange(nodes: List[Gaffer.Node], parent: Optional[Gaffer.Node] = None):
    """Layout the nodes in the graph.

    Args:
        nodes (list): The nodes to rearrange into a nice layout.
        parent (list[Gaffer.Node]): Optional. The parent node to layout in.
            If not provided the parent of the first node is taken. The
            assumption is made that all nodes reside within the same parent.

    Returns:
        None

    """
    import GafferUI

    if not nodes:
        return

    if parent is None:
        # Assume passed in nodes all belong to single parent
        parent = nodes[0]

    graph = GafferUI.GraphGadget(parent)
    graph.getLayout().layoutNodes(graph, Gaffer.StandardSet(nodes))


def traverse_scene(scene_plug: GafferScene.ScenePlug,
                   root: str = "/") -> Iterator[str]:
    """Yields breadth first all children from given `root`.

    Note: This also yields the root itself.
    This traverses down without the need for a recursive function.

    Args:
        scene_plug (GafferScene.ScenePlug): Plug scene to traverse.
            Typically, the out plug of a node (`node["out"]`).
        root (string): The root path as starting point of the traversal.

    Yields:
        str: Child path

    """
    queue = SimpleQueue()
    queue.put_nowait(root)
    while not queue.empty():
        path = queue.get_nowait()
        yield path

        for child_name in scene_plug.childNames(path):
            child_path = f"{path.rstrip('/')}/{child_name}"
            queue.put_nowait(child_path)


def find_camera_paths(scene_plug: GafferScene.ScenePlug,
                      root: str = "/") -> List[str]:
    """Traverses the scene plug starting at `root` returning all cameras.

    Args:
        scene_plug (GafferScene.ScenePlug): Plug scene to traverse.
            Typically, the out plug of a node (`node["out"]`).
        root (string): The root path as starting point of the traversal.

    Returns:
        List[str]: List of found paths to cameras.

    """
    return find_paths_by_type(scene_plug, "Camera", root)


def find_paths_by_type(scene_plug: GafferScene.ScenePlug,
                       object_type_name: str,
                       root: str = "/") -> List[str]:
    """Return all paths in scene plug under `path` that match given type.

    Examples:
        >>> find_paths_by_type(plug, "MeshPrimitive")  # all meshes
        # ['/cube', '/nested/path/cube']
        >>> find_paths_by_type(plug, "NullObject")     # all nulls (groups)
        # ['/nested/path']
        >>> find_paths_by_type(plug, "Camera")         # all cameras
        # ['/camera', /nested/camera2']

    Args:
        scene_plug (GafferScene.ScenePlug): Plug scene to traverse.
            Typically, the out plug of a node (`node["out"]`).
        object_type_name (String): The name of the object type we want to find.
        root (string): Starting root path of traversal.

    Returns:
        List[str]: List of found paths matching the object type name.

    """
    result = []
    for path in traverse_scene(scene_plug, root):
        if scene_plug.object(path).typeName() == object_type_name:
            result.append(path)
    return result


def get_color_management_preferences(script_node):
    """Get default OCIO preferences"""
    return {
        "config": script_node['openColorIO']['config'].getValue(),
        "display": script_node['openColorIO']['displayTransform'].getValue(),
        "view": script_node['openColorIO']['workingSpace'].getValue()
    }


def set_frame_range(script_node,
                    include_handles=True):

    frame_start = script_node.context().get("ayon:frame_start")
    frame_end = script_node.context().get("ayon:frame_end")
    handle_start = script_node.context().get("ayon:handle_start")
    handle_end = script_node.context().get("ayon:handle_end")

    if include_handles:
        frame_start -= handle_start
        frame_end += handle_end
    log.info(f"Setting frame range: [{frame_start}-{frame_end}")
    script_node["frameRange"]["start"].setValue(int(frame_start))
    script_node["frameRange"]["end"].setValue(int(frame_end))

    # if we are in a GUI session we also reset the frame slider
    application = script_node.ancestor(Gaffer.ApplicationRoot)
    if application:
        import GafferUI
        playback = GafferUI.Playback.acquire(script_node.context())
        playback.setFrameRange(frame_start, frame_end)


def set_framerate(script_node):
    fps = script_node.context().get("ayon:fps")
    if fps is None:
        log.warning("NO FRAMERATE")
        return

    script_node['framesPerSecond'].setValue(fps)
    log.info(f"Set framerate to [{fps}]")


def update_root_context_variables(script_node, project_name, asset_name):
    folder = next(ayon_api.get_folders(
        project_name,
        folder_paths=[asset_name])
    )
    fps = folder["attrib"]["fps"]
    res_x = folder["attrib"]["resolutionWidth"]
    res_y = folder["attrib"]["resolutionHeight"]
    frame_start = folder["attrib"]["frameStart"]
    frame_end = folder["attrib"]["frameEnd"]
    handle_start = folder["attrib"]["handleStart"]
    handle_end = folder["attrib"]["handleEnd"]

    set_root_context_variables(script_node, {
        "fps": fps,
        "resolution": (res_x, res_y),
        "frame_start": frame_start,
        "frame_end": frame_end,
        "handle_start": handle_start,
        "handle_end": handle_end,
    })


def replace_node(old_node, new_node, ignore_plug_names=[], rename=True):
    all_plugs = []
    get_all_plugs(old_node, all_plugs)
    ignore_plug_names += ["globals"]
    plug_data = {}
    for plug in all_plugs:
        if plug.getName() in ignore_plug_names:
            continue

        if not bool(plug.getFlags() & Gaffer.Plug.Flags.Serialisable):
            log.debug(f"Throwing out non-serializable {plug.getName()}")
            continue
        try:
            plug_data[plug] = plug.getValue()
        except Exception:
            pass

    # first store old connections
    with Gaffer.UndoScope(old_node.scriptNode()):
        connections = get_node_connections(old_node)
        for src, pluginfo in connections.items():
            source_plug = new_node
            for part in src.split('.'):
                if source_plug is None:
                    continue
                source_plug = source_plug.getChild(part)

            for plug in pluginfo['in']:
                if source_plug is None:
                    log.debug(f"! {src} is None")
                    continue
                source_plug.setInput(plug)
            for plug in pluginfo['out']:
                plug.setInput(source_plug)

        for plug, value in plug_data.items():
            plug_relative_name = plug.fullName().replace(
                plug.node().fullName(), "")[1:]  # strip out the prefix .

            target_plug = new_node
            for part in plug_relative_name.split("."):
                try:
                    target_plug = target_plug[part]
                except KeyError:
                    target_plug = None
                    break


            if target_plug is None:
                # the target plug does not exist. we need to create it
                copy_plug(plug, new_node)
            else:
                if not bool(target_plug.getFlags() &
                            Gaffer.Plug.Flags.Serialisable):
                    log.debug(f"Skipping non-serializable plug {target_plug}")
                    continue
                try:
                    # log.debug(f"Setting {target_plug.fullName()} to {value}")
                    target_plug.setValue(value)
                except Exception as err:
                    log.debug(f"Error setting [{target_plug}]={value}: {err}")
        old_name = old_node.getName()
        new_node.scriptNode().removeChild(old_node)
        new_node.setName(old_name)
        # and finally we have a hack to avoid `scene:path` errors on some
        # upstream nodes after replacing a node
        for n in Gaffer.NodeAlgo.upstreamNodes(new_node):
            try:
                before = n["enabled"].getValue()
                n["enabled"].setValue(False)
                n["enabled"].setValue(True)
                n["enabled"].setValue(before)
            except Exception:
                pass


def copy_plug(plug, destination_node):
    log.debug(f"Copying plug [{plug}] to {destination_node}")
    try:
        src_node = plug.node()

        plug_path = plug.fullName().replace(src_node.fullName(), "").strip(".")
        plug_parts = plug_path.split('.')[:-1]
        new_plug_parent = destination_node
        for part in plug_parts:
            new_plug_parent = new_plug_parent[part]

        new_plug = type(plug)(
            plug.getName(),
            defaultValue=plug.defaultValue(),
            flags=plug.getFlags()
        )
        new_plug_parent.addChild(new_plug)

        metadata_keys = Gaffer.Metadata.registeredValues(plug)
        for key in metadata_keys:
            value = Gaffer.Metadata.value(plug, key)
            log.debug(f"Copying metadata {key}:{value} to {new_plug}")
            Gaffer.Metadata.registerValue(new_plug, key, value)
    except Exception as err:
        log.error(f"Could not copy plug: {plug.getName()} to"
                  f"{destination_node}: {err}")


def get_all_plugs(in_node, thelist):
    for plug in in_node.children(Gaffer.Plug):
        thelist.append(plug)
        if len(plug.children(Gaffer.Plug)) > 0:
            get_all_plugs(plug, thelist)


def get_node_connections(node, include_non_serializable=False):
    '''
    Returns a dictionary of all plugs connected to node `node`, example:

    it is of the form
    {
        'parameter relative path to `node`': {
            'in': [list of input plugs]
            'out': [list of output plugs]
        }
    }

    {
        'out.lensdistort_path': # fullName for plug on input node
        {
            'in': [], # list of plugs that 'out.lensdistort_path' has as inputs
            'out': [  # list of plugs that 'out.lensdistort_path' has as outputs
                Gaffer.StringPlug( "fileName", defaultValue = '', substitutions = IECore.StringAlgo.Substitutions.VariableSubstitutions | IECore.StringAlgo.Substitutions.EscapeSubstitutions | IECore.StringAlgo.Substitutions.TildeSubstitutions )
            ]
        },
        'out.render_path':
        {
            'in': [],
            'out': [
                Gaffer.StringPlug( "text", defaultValue = 'Hello World', )
            ]
        }
    }

    '''

    all_the_plugs = []
    get_all_plugs(node, all_the_plugs)
    plugs = {}
    for plug in all_the_plugs:
        the_input = plug.getInput()
        outputs = plug.outputs()
        if not include_non_serializable and not bool(plug.getFlags() & Gaffer.Plug.Flags.Serialisable):
            continue


        plugmap = {'in': [], 'out': []}
        if the_input is not None:
            if not node.isAncestorOf(the_input):
                plugmap['in'].append(the_input)
        for o in outputs:
            if o.node() == node or node.isAncestorOf(o):
                continue
            plugmap['out'].append(o)
        if the_input is None and len(outputs) == 0:
            continue
        if len(plugmap["in"]) == len(plugmap["out"]) == 0:
            continue
        plugs[plug.relativeName(node)] = plugmap
    return plugs


def set_root_context_variables(script_node, var_dict):
    context_vars = script_node["variables"]
    existing_ayon_variables = [var["name"].getValue() for var in context_vars.children()]
    for var_name, var_data in var_dict.items():
        if isinstance(var_data, (tuple, list)):
            # ok we got a vector of sorts
            if len(var_data) == 2:
                plug_type = Gaffer.V2iPlug
                default_value = imath.V2i(0, 0)
                var_data = imath.V2i(var_data[0], var_data[1])
        elif isinstance(var_data, int):
            plug_type = Gaffer.IntPlug
            default_value = var_data
        elif isinstance(var_data, float):
            plug_type = Gaffer.FloatPlug
            default_value = var_data
        else:
            raise RuntimeError(
                f"Unknown data type [{var_data}] for variable {var_name}")

        if not var_name.startswith("ayon:"):
            var_name = f"ayon:{var_name}"

        if var_name not in existing_ayon_variables:
            context_vars.addChild(
                Gaffer.NameValuePlug(
                    var_name,
                    plug_type(
                        var_name,
                        defaultValue=default_value,
                        flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
                    ),
                    var_name
                )
            )

        context_vars[var_name]["value"].setValue(var_data)
