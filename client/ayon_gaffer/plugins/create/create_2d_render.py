import copy
import os
import pathlib

import Gaffer

from ayon_core.pipeline import CreatedInstance
from ayon_gaffer.api import plugin
from ayon_core.lib import BoolDef, NumberDef, StringTemplate
from ayon_gaffer.api.lib import get_work_default_directory

from ayon_gaffer.api.nodes.render_2d import RenderNode2D


class CreateGaffer2DRender(plugin.GafferCreatorBase):
    identifier = "io.ayon.creators.gaffer.render2d"
    deprecated_identifiers = ["io.openpype.creators.gaffer.render2d"]
    label = "2DRender"
    product_type = "render2d"
    description = "C2D Render"
    icon = "fa5.film"

    def _update_write_node_filepath(self, created_inst, script):

        data = created_inst.data_to_store()

        formatting_data = copy.deepcopy(data)
        formatting_data.update({"ext": "exr"})

        # todo find the template in the settings
        temp_rendering_path_template = (
            "{work}/renders/gaffer/{product[name]}.{frame}.{ext}")

        file_name = str(script["fileName"].getValue())

        fpath_template = temp_rendering_path_template
        formatting_data["work"] = get_work_default_directory(formatting_data, file_name)
        fpath = StringTemplate(fpath_template).format_strict(formatting_data)

        staging_dir = self.apply_staging_dir(created_inst)
        if staging_dir:
            basename = os.path.basename(fpath)
            staging_path = pathlib.Path(staging_dir)/ basename
            fpath = staging_path.as_posix()

        return fpath

    def _create_node(self,
                     product_name: str,
                     pre_create_data: dict,
                     script: Gaffer.ScriptNode) -> Gaffer.Node:

        node = RenderNode2D(product_name)
        script.addChild(node)

        if pre_create_data.get("use_selection", False) and len(self.selected_nodes) >= 1:
            node["in"].setInput(self.selected_nodes[0]["out"])

        frame_start, frame_end = self._get_frame_range()
        node["startFrame"].setValue(frame_start)
        node["endFrame"].setValue(frame_end)

        data = {}
        data["folderPath"] = self.create_context.host.get_current_folder_path()
        data["task"] = self.create_context.host.get_current_task_name()
        data["variant"] = data["task"].title()
        ctx_data = self.create_context.host.get_context_data()
        data.update(ctx_data)

        instance = CreatedInstance(
            product_type=self.product_type,
            product_name="renderLayoutMain",
            data=data,
            creator=self
        )
        path = self._update_write_node_filepath(instance, script)
        node["fileName"].setValue(path)

        return node

    def _get_frame_range(self):
        task_entity = self.create_context.get_current_folder_entity()
        return task_entity["attrib"]["frameStart"], task_entity["attrib"]["frameEnd"]

    def get_instance_attr_defs(self):
        frame_start, frame_end = self._get_frame_range()

        return [
            BoolDef(
                "farm_rendering",
                default=True,
                label="Farm rendering"
            ),
            NumberDef("frameStart",
                      label="Frame Start",
                      default=frame_start,
                      decimals=0),
            NumberDef("frameEnd",
                      label="Frame End",
                      default=frame_end,
                      decimals=0),
        ]