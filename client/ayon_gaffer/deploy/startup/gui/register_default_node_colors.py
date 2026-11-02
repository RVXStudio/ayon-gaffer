import importlib
import inspect

import Gaffer
import imath

from ayon_core.settings import get_project_settings
from ayon_core.lib import Logger
from ayon_core.pipeline import get_current_project_name


log = Logger.get_logger("ayon_gaffer.register_default_node_colors")

project_name = get_current_project_name()
settings = get_project_settings(project_name)
color_settings = settings.get("gaffer", {}).get("node_colors", {})

def get_node_class(node_class):
    """
    Claude authored.
    
    Resolve e.g. "GafferImage.Clamp" to the GafferImage.Clamp class.
    """
    module_name, _, class_name = node_class.rpartition(".")
    if not module_name:
        raise ValueError(f"Expected 'Module.Class', got {node_class!r}")
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    if not (inspect.isclass(cls) and issubclass(cls, Gaffer.Node)):
        raise TypeError(f"{node_class} is not a Gaffer.Node subclass")
    return cls


def get_all_nodes_from_package(module):
    """
    Claude authored. Get's all creatable nodes from the given module.

    Args:
        module: str or module
    """

    if isinstance(module, str) :
        module = importlib.import_module(module)

    for name in sorted(dir(module)) :

        cls = getattr(module, name)
        if not inspect.isclass(cls) or not issubclass(cls, Gaffer.Node) :
            continue
        if name.startswith("_") :
            continue

        try :
            node = cls()
        except Exception:
            continue

        if not cls.__module__.startswith(module.__name__ + ".") :
            continue

        if name != node.typeName().rpartition(":")[2] :
            continue

        yield cls

def set_node_color(cls, color):
    log.debug(f"Setting metadata nodeGadget:color for [{cls}] to {color}")
    Gaffer.Metadata.registerValue(cls,  "nodeGadget:color", imath.Color3f(color[0], color[1], color[2]))

def colorize_package_nodes(package_name, color):
    try:
        for cls in get_all_nodes_from_package(package_name) :
            set_node_color(cls, color)
    except Exception:
        log.exception(f"Could not register color {color} for {package_name}")

def colorize_nodes(node_class_list, color):
    for node_class in node_class_list:
        try:
            cls = get_node_class(node_class)
            set_node_color(cls, color)
        except Exception:
            log.exception(f"Could not register color {color} for node {node_class}")

# first packages
for package_info in color_settings.get("packages", []):
    pkg_name = package_info["package_name"]
    color = package_info["color"]
    log.info(f"Registering nodes of [{pkg_name}] to have color {color}")
    colorize_package_nodes(pkg_name, color)


# then node overrides
for node_info in color_settings.get("nodes", []):
    log.info(f"Node: {node_info}")
    node_classes = node_info["node_classes"]
    color = node_info["color"]

    colorize_nodes(node_classes, color)