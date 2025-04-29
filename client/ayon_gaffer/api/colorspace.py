import attr

from ayon_gaffer.api.lib import get_color_management_preferences
from ayon_core.pipeline.colorspace import (
    get_imageio_file_rules_colorspace_from_filepath,
    get_current_context_imageio_config_preset,
)
from ayon_core.lib import Logger
log = Logger.get_logger('ayon_gaffer.api.colorspace')


@attr.s
class LayerMetadata(object):
    """Data class for Render Layer metadata."""
    pass


@attr.s
class RenderProduct(object):
    """Getting Colorspace as
    Specific Render Product Parameter for submitting
    publish job.

    """
    colorspace = attr.ib()                      # colorspace
    view = attr.ib()
    display = attr.ib()
    productName = attr.ib(default=None)


class ARenderProduct(object):

    def __init__(self, script_node, aovs):
        """Constructor."""
        # Initialize
        self.script_node = script_node
        self.aovs = aovs
        self.layer_data = self._get_layer_data()
        self.layer_data.products = self.get_colorspace_data()

    def _get_layer_data(self):
        return LayerMetadata(
        )

    def get_colorspace_data(self):
        """To be implemented by renderer class.

        This should return a list of RenderProducts.

        Returns:
            list: List of RenderProduct

        """
        data = get_color_management_preferences(self.script_node)
        colorspace_data = []
        for aov in self.aovs:
            colorspace_data.append(
                RenderProduct(
                    colorspace=self.simplify_colorspace_names(
                        data["colorspace"]),
                    view=data["view"],
                    display=data["display"],
                    productName=aov
                ))
        return colorspace_data

    def simplify_colorspace_names(self, colorspace_name):
        replacements = {"ACES - ACEScg": "acescg", "ACES - ACES2065-1": "aces"}
        for k, v in replacements.items():
            if colorspace_name == k:
                print(f"replacing {colorspace_name} with {v}")
                return v
        return colorspace_name


def get_representation_colorspace_data(
        project_name, repre_entity, filepath
        ):
    """Get colorspace data from representation documents or filepath

    Args:
        project_name (str): Project name.
        repre_entity (dict): Representation entity.
        filepath (str): File path.

    Returns:
        Any[str,None]: colorspace name or None
    """

    colorspace = repre_entity["data"].get("colorspaceData", {}).get(
        "colorspace")
    log.debug(
        f"Colorspace from representation colorspaceData: {colorspace}"
    )

    config_data = get_current_context_imageio_config_preset()
    # check if any filerules are not applicable
    new_parsed_colorspace = get_imageio_file_rules_colorspace_from_filepath( # noqa
        filepath, "gaffer", project_name, config_data=config_data
    )
    log.debug(f"Colorspace new filerules: {new_parsed_colorspace}")

    return (
        new_parsed_colorspace
        or colorspace
    )
