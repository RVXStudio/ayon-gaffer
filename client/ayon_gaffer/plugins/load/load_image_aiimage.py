from ayon_core.pipeline import (
    get_representation_path,
)
import ayon_gaffer.api.lib
import ayon_gaffer.api.utils
import ayon_gaffer.api.plugin
import ayon_gaffer.api.colorspace
import ayon_gaffer.api.pipeline


class GafferLoadImageAiImage(ayon_gaffer.api.plugin.GafferImageLoaderBase):
    """Load an AiImage"""

    product_types = ["image"]
    representations = ["*"]

    label = "Load sequence (AiImage)"
    order = -10
    icon = "code-fork"
    color = "orange"

    @classmethod
    def apply_settings(cls, project_settings):
        super(GafferLoadImageAiImage, cls).apply_settings(project_settings)

        try:
            # check if we can import GafferArnold -> is Arnold loaded?
            import GafferArnold  # noqa
        except ModuleNotFoundError:
            # if not we just disable this loader quietly
            print("GafferArnold not available; disable GafferLoadImageAiImage")
            cls.enabled = False

    def load(self, context, name, namespace, data):
        import GafferArnold  # we need to load it here to avoid erroring
        # Create the Loader with the filename path set
        node = GafferArnold.ArnoldShader("image")
        node.loadShader("image")

        path = self.filepath_from_context(context)
        path = self._convert_path(path)
        node["parameters"]["filename"].setValue(path)

        self.set_up_node(name, namespace, node, context)

        self.set_node_colorspace(
            node["parameters"]["color_space"],
            context,
            path)

    def update(self, container, context):
        representation = context["representation"]

        path = get_representation_path(representation)
        path = self._convert_path(path)

        node = container["_node"]
        node["parameters"]["filename"]  .setValue(path)

        # Update the imprinted representation
        node["user"]["representation"].setValue(str(representation["id"]))

        self.set_node_colorspace(
            node["parameters"]["color_space"],
            context,
            path)
