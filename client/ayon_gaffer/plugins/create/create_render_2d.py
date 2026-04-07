import copy
import os
import pathlib

import Gaffer

from ayon_core.lib import EnumDef, NumberDef, StringTemplate
from ayon_core.pipeline import CreatedInstance, get_current_context
from ayon_core.settings import get_project_settings

from ayon_gaffer.api import plugin
from ayon_gaffer.api.lib import get_work_default_directory
from ayon_gaffer.api.nodes.lib import BoxNodeManagerInstance


class CreateGafferRender2D(plugin.GafferCreatorBase):
    identifier = "io.ayon.creators.gaffer.render2d"
    deprecated_identifiers = ["io.openpype.creators.gaffer.render2d"]
    label = "Render2D"
    product_type = "render"
    product_base_type = "render"
    description = "Render 2D"
    icon = "fa5.film"
    strip_task = False

    def _update_write_node_filepath(self, created_inst, script):

        data = created_inst.data_to_store()

        formatting_data = copy.deepcopy(data)
        formatting_data.update({"ext": "exr"})
        project_name = get_current_context()["project_name"]
        project_settings = get_project_settings(project_name)
        temp_rendering_path_template = (
            project_settings["gaffer"]
            .get("create", {})
            .get("CreateRender2d", {})
            .get("temp_rendering_path_template", "{work}/renders/gaffer/{product[name]}.{frame}.{ext}")
        )
        file_name = str(script["fileName"].getValue())

        fpath_template = temp_rendering_path_template
        formatting_data["work"] = get_work_default_directory(formatting_data, file_name)
        fpath = StringTemplate(fpath_template).format_strict(formatting_data)
        staging_dir = self.apply_staging_dir(created_inst)
        if staging_dir:
            basename = os.path.basename(fpath)
            staging_path = pathlib.Path(staging_dir) / basename
            fpath = staging_path.as_posix()

        return fpath

    def _create_node(
        self,
        product_name: str,
        pre_create_data: dict,
        script: Gaffer.ScriptNode,
        instance=None,
    ) -> Gaffer.Node:

        node = BoxNodeManagerInstance.create(script, "Render2D", "1")
        script.addChild(node)

        if pre_create_data.get("use_selection", False) and len(self.selected_nodes) >= 1:
            node["in"].setInput(self.selected_nodes[0]["out"])

        frame_start, frame_end, handle_start, handle_end = self._get_frame_range()
        node["startFrame"].setValue(frame_start - handle_start)
        node["endFrame"].setValue(frame_end + handle_end)

        path = self._update_write_node_filepath(instance, script)
        node["fileName"].setValue(path)

        return node

    def _get_frame_range(self):
        task_entity = self.create_context.get_current_folder_entity()
        return (
            task_entity["attrib"]["frameStart"],
            task_entity["attrib"]["frameEnd"],
            task_entity["attrib"]["handleStart"],
            task_entity["attrib"]["handleEnd"],
        )

    def get_instance_attr_defs(self):

        rendering_targets = {}
        rendering_targets["local"] = "Local machine rendering"
        rendering_targets["frames"] = "Use existing frames"
        rendering_targets["farm"] = "Farm rendering"
        rendering_targets["frames_farm"] = "Use existing frames - farm"

        return [EnumDef("render_target", items=rendering_targets, label="Render target")]

    def update_instances(self, update_list):
        super(CreateGafferRender2D, self).update_instances(update_list)
        for created_inst, _changes in update_list:
            node = created_inst.transient_data["node"]
            script_node = node.scriptNode()
            new_path = self._update_write_node_filepath(created_inst, script_node)
            node["fileName"].setValue(new_path)
