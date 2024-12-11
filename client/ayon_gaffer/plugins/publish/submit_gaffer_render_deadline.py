import os
import copy
import re
import json
import getpass
from datetime import datetime

import requests
import pyblish.api


from ayon_core.pipeline import AYONPyblishPluginMixin

from ayon_core.lib import (
    BoolDef,
    NumberDef,
    Logger,
    TextDef,
    EnumDef
)

import GafferDeadline
import Gaffer
import GafferDispatch

import ayon_gaffer.api.lib
import ayon_gaffer.api.pipeline

log = Logger.get_logger("ayon_gaffer.plugins.publish.submit_gaffer_render_deadline")


class GafferSubmitDeadline(pyblish.api.InstancePlugin,
                           AYONPyblishPluginMixin):
    """Submit write to Deadline

    Renders are submitted via GafferDeadline

    """

    label = "Submit Gaffer to Deadline"
    order = pyblish.api.IntegratorOrder + 0.1
    hosts = ["gaffer"]
    families = ["render"]
    optional = True
    targets = ["local"]

    # presets
    priority = 50
    chunk_size = 1
    concurrent_tasks = 1
    group = ""
    primary_pool = ""
    secondary_pool = ""
    department = ""
    limit_groups = {}
    use_gpu = False
    env_allowed_keys = []
    env_search_replace_values = {}
    workfile_dependency = True

    limits = ""
    suspended = False

    env_vars_to_submit = {
        "ARNOLD_ROOT": "",
        "AYON_RENDER_JOB": "1",
        "FTRACK_API_KEY": "",
        "FTRACK_API_USER": "",
        "FTRACK_SERVER": "",
        "AYON_PROJECT_NAME": "",
        "AYON_FOLDER_PATH": "",
        "AYON_TASK_NAME": "",
        "AYON_APP_NAME": "",
        "AYON_BUNDLE_NAME": "",
        "DEADLINE_ENVIRONMENT_CACHE_DIR": "",
    }

    @classmethod
    def apply_settings(cls, project_settings):
        settings = project_settings["gaffer"]["deadline"]["default_submission_settings"]  # noqa
        cls.priority = settings["priority"]
        cls.limit_groups = project_settings["gaffer"]["deadline"]["limit_groups"]

    @classmethod
    def get_attribute_defs(cls):
        limit_groups = [""] + ayon_gaffer.api.pipeline.DEADLINE_LIMIT_GROUPS
        return [
            NumberDef(
                "priority",
                label="Priority",
                default=cls.priority,
                decimals=0
            ),
            BoolDef(
                "suspended",
                default=False,
                label="Suspend Render"
            ),
            EnumDef(
                "limits",
                default="",
                items=limit_groups,
                multiselection=True,
                label="Limits"
            )

        ]

    def process(self, instance):
        if not instance.data.get("farm"):
            self.log.debug("Skipping local instance.")
            return
        instance.data["attributeValues"] = self.get_attr_values_from_data(
            instance.data)

        # families = instance.data["families"]
        frames = instance.data['frameList']

        # set the publish priority to follow the given priority
        instance.data["priority"] = instance.data["attributeValues"].get(
            "priority", self.priority)

        node = instance.data["transientData"]["node"]

        self.log.info(f"Submitting {node}")
        with node.scriptNode().context() as ctxt:
            render_shot_name = instance.data["folderPath"].split("/")[-1]
            # create a dispatcher
            dispatcher = GafferDeadline.DeadlineDispatcher()
            # set some dispatcher settings
            job_name = ctxt.substitute('${script:name}')
            job_directory = ctxt.substitute(
                '${project:rootDirectory}/dispatcher/deadline'
                )
            self.log.info(f"Job name: {job_name}, dir: {job_directory}")
            dispatcher['jobName'].setValue(job_name)
            dispatcher['jobsDirectory'].setValue(job_directory)

            dispatcher['framesMode'].setValue(2)
            dispatcher['frameRange'].setValue(
                ','.join([str(f) for f in frames])
            )
            self.log.info(
                f"{dispatcher['framesMode'].getValue()}; "
                "{dispatcher['frameRange'].getValue()}"
            )
            self.populate_dispatcher_env_vars(node)

            # clear the dispatcher limits plug, since we construct it with
            # the arnold limit, the calculated limit groups and user input
            self.clear_limits(node)
            # these methods add their results to their respective task node
            # limits knob for the deadline dispatcher.
            self.add_arnold_limits(node)
            self.add_limit_groups(node)
            saved_settings = self.apply_submission_settings(node, instance)

            saved_context_vars = self.set_render_context_vars(
                node, render_shot_name)

            dispatcher.dispatch([node])

            self.restore_render_context_vars(node, saved_context_vars)

            self.clear_dispatcher_env_vars(node)
            self.restore_submission_settings(node, saved_settings)

            submitted_jobs = [job for job in dispatcher._deadlineJobs
                              if job._jobId is not None]

            # if the job is zero frames or not doing anything, then it gets a
            # job id of None
            if len(submitted_jobs) == 0:
                # we submitted no jobs
                raise Exception('No jobs were submitted, check framerange')

            # since GafferDeadline has it's own job class, we need to map from
            # that one to the proper Deadline job class used in other places
            # within Ayon
            fake_deadline_job = {}
            for j in submitted_jobs:
                self.log.info(f'submitted job {j._jobId}')
            last_submitted_job = submitted_jobs[-1]
            fake_deadline_job["_id"] = last_submitted_job._jobId
            fake_deadline_job["Props"] = {
                "Env": last_submitted_job._environmentVariables.copy(),
                "Batch": job_name,
                "User": instance.context.data.get(
                    "deadlineUser", getpass.getuser())
            }

            instance.data["deadlineSubmissionJob"] = fake_deadline_job
            instance.data["deadlineSubmissionWaitForIds"] = [j._jobId for j in submitted_jobs]

    def get_env_var_value(self, var, val):
        if val == '':
            return os.environ.get(var, '')
        else:
            return val

    def populate_dispatcher_env_vars(self, root_node):
        self.log.info(f"Setting env vars for {root_node} ...")

        for node in root_node.children(GafferDispatch.TaskNode):
            try:
                env_var_plug = node['dispatcher']['deadline']['environmentVariables']
            except KeyError:
                log.error(f"No dispatcher settings found on {node}")
                continue
            existing_var_plugs = {var['name'].getValue(): var for var in env_var_plug.children()}
            self.log.info(f"- Setting vars for {node}")

            for var, value in self.env_vars_to_submit.items():
                if var not in existing_var_plugs.keys():
                    the_plug = Gaffer.NameValuePlug(var,
                        Gaffer.StringPlug("varval",defaultValue='', flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic),
                        True,
                        "env_var",
                        Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
                    )
                    env_var_plug.addChild(the_plug)
                else:
                    the_plug = existing_var_plugs[var]
                the_plug['value'].setValue(self.get_env_var_value(var, value))
        self.log.info('... done!')

    def clear_dispatcher_env_vars(self, root_node):
        self.log.info(f"Clearing env vars for {root_node} ...")
        for node in root_node.children(GafferDispatch.TaskNode):
            try:
                deadline_env_plug = node['dispatcher']['deadline']['environmentVariables']
            except KeyError:
                # something is missing.
                continue
            self.log.info(f"- Clearing vars for {node}")
            for plug in deadline_env_plug.children():
                if plug['name'].getValue() in self.env_vars_to_submit.keys():
                    deadline_env_plug.removeChild(plug)
        self.log.info('... done!')

    def add_arnold_limits(self, root_node):
        """
        Traverses the script for either ArnoldRender nodes or Render nodes set
        to "Arnold", if they are found add the "arnold" limit to the deadline
        submission
        """
        try:
            import GafferScene
        except ModuleNotFoundError:
            # no arnold
            return

        for node in root_node.children(GafferScene.Render):
            self.log.info(f"Arnold limit search: {node}")
            if node.typeName() == "GafferScene::Render":
                try:
                    if node["renderer"] != "Arnold":
                        # this is not an arnold render node, ignore it
                        continue
                except KeyError:
                    # there is no renderer plug, abort, abort!
                    continue
            try:
                limit_plug = node['dispatcher']['deadline']['limits']
            except KeyError as err:
                # something is wrong here, can't find either "deadline"
                # or "limits"
                log.error(f"Could not find deadline dispatcher plugs: {err}")
                continue
            self.log.info("made it!")
            ayon_gaffer.api.lib.append_to_csv_plug(limit_plug, "arnold")

    def add_limit_groups(self, root_node):
        if len(self.limit_groups) == 0:
            # no limit groups, nothing to check!
            return

        script_node = root_node.scriptNode()
        all_nodes = ayon_gaffer.api.lib.get_all_children(script_node)

        # first see if we have interesting nodes in here
        active_node_types = set()
        for node in all_nodes:
            tn = node.typeName()
            if tn in active_node_types:
                continue
            if "enabled" not in node.keys():
                self.log.debug(f"No enabled on {node}")
                continue
            if node["enabled"].getValue():
                active_node_types.add(tn)
        limits_to_add = []
        for limit_group in self.limit_groups:
            limit_name = limit_group["name"]

            for type_name in limit_group["value"]:
                if type_name in active_node_types:
                    limits_to_add.append(limit_name)
                    break

        if len(limits_to_add) > 0:
            self.log.info(f"Adding limits {limits_to_add}")
            for node in root_node.children(GafferDispatch.TaskNode):
                limit_plug = node['dispatcher']['deadline']['limits']
                ayon_gaffer.api.lib.append_to_csv_plug(
                    limit_plug, ",".join(limits_to_add))

    def clear_limits(self, root_node):
        for node in root_node.children(GafferDispatch.TaskNode):
            deadline_settings_plug = node['dispatcher']['deadline']
            self.log.debug(
                f"Clearing dispatcher limits for [{node.getName()}]")
            deadline_settings_plug["limits"].setValue("")

    def get_submission_settings(self, node, instance, default_settings):
        project_settings = instance.context.data["project_settings"]
        task_node_settings = (project_settings["gaffer"]["deadline"]
                              ["task_node_submission_settings"])

        submission_settings = copy.copy(default_settings)
        for entry in task_node_settings:
            # first we check the node typeName
            for task_entry in entry["task_node"]:
                matching_node = False
                for type_name in task_entry["type_names"]:
                    if node.typeName() == type_name:
                        matching_node = True
                        # self.log.info(f"Found type {type_name}")
                        # now we can check the other filters
                        for plug in task_entry["plugs"]:
                            pname = plug["name"]
                            plug_type = plug["type"]
                            if pname in node.keys():
                                if node[pname].getValue() != plug[plug_type]:
                                    matching_node = False
                if matching_node:
                    self.log.info(f"Insteresting node {node}")
                    node_settings = entry["submission_settings"]
                    submission_settings["priority"] = node_settings["priority"]
                    submission_settings["pool"] = node_settings["primary_pool"]
                    submission_settings["secondaryPool"] = node_settings["secondary_pool"]
                    submission_settings["group"] = node_settings["group"]
                    return submission_settings
        return submission_settings


    def apply_submission_settings(self, root_node, instance):
        self.log.info(
            f"Applying submission settings for"
            f"[{root_node.getName()}]"
        )

        # get the default settings, that _might_ be changed by per-node
        # overrides in the settings
        default_submission_settings = self.collect_submission_settings(
            instance)

        saved_values = {}
        for node in root_node.children(GafferDispatch.TaskNode):
            self.log.info(f" ** {node.getName()} **")
            # check if we have task node type specific submission settings
            node_submission_settings = self.get_submission_settings(
                node, instance, default_submission_settings)
            self.log.info(json.dumps(node_submission_settings, indent=4))

            # store the existing settings so we can reset them after submission
            deadline_settings_plug = node['dispatcher']['deadline']
            current_settings = {}
            for plug in deadline_settings_plug.children():
                if plug.typeName() == 'Gaffer::CompoundDataPlug':
                    continue
                current_settings[plug.getName()] = plug.getValue()
            saved_values[node.getName()] = current_settings

            # now se set the values
            for key, value in node_submission_settings.items():
                log.debug(f"Setting [{key}] to [{value}]")
                if key == "limits":
                    ayon_gaffer.api.lib.append_to_csv_plug(
                        deadline_settings_plug["limits"], value)
                else:
                    deadline_settings_plug[key].setValue(value)

        return saved_values

    def restore_submission_settings(self, root_node, old_settings):
        self.log.info(
            f"Restoring submission settings for"
            f"[{root_node.getName()}]"
        )

        for node in root_node.children(GafferDispatch.TaskNode):
            log.info(f" !! {node.getName()} !!")
            deadline_settings = node['dispatcher']['deadline']
            current_settings = old_settings[node.getName()]
            for key, value in current_settings.items():
                deadline_settings[key].setValue(value)

    def get_last_context_var_node(self, root_node):
        plugs = root_node.children(GafferDispatch.TaskNode.TaskPlug)
        task_out_plug = None
        for plug in plugs:
            if plug.direction() == Gaffer.Plug.Direction.Out:
                task_out_plug = plug
                break
        else:
            raise RuntimeError(
                f"Could not find a TaskPlug output for {root_node}")
        task_out_plug_input = task_out_plug.getInput()
        if task_out_plug_input is None:
            raise RuntimeError(
                f"Nothing inside {root_node} is connected to {task_out_plug}"
                )
        context_var_nodes = Gaffer.NodeAlgo.upstreamNodes(
            task_out_plug_input.node(), Gaffer.ContextVariables)
        if len(context_var_nodes) == 0:
            # for now we can't insert context variable nodes so we error
            raise RuntimeError(
                f"No ContextVariables node found in {root_node}")
        return context_var_nodes[0]

    def set_render_context_vars(self, root_node, render_shot):
        self.log.info(f"Setting render context var {root_node}")
        # first find the task output plug
        context_var_node = self.get_last_context_var_node(root_node)
        if "render:shot" not in context_var_node["variables"].keys():
            self.log.info("no render:shot in node, creating")
            render_shot_plug = ayon_gaffer.api.lib.create_render_shot_plug()
            context_var_node["variables"].addChild(render_shot_plug)
        else:
            self.log.info('render:shot in node!')
            render_shot_plug = context_var_node["variables"]["render:shot"]

        old_render_shot_value = render_shot_plug["value"].getValue()
        old_render_shot_enabled = render_shot_plug["enabled"].getValue()
        render_shot_plug["value"].setValue(render_shot)
        self.log.info(f'setting render:shot to {render_shot}')
        render_shot_plug["enabled"].setValue(True)
        return {"render:shot": {"value": old_render_shot_value,
                                "enabled": old_render_shot_enabled}}

    def restore_render_context_vars(self, root_node, old_settings):
        context_var_node = self.get_last_context_var_node(root_node)
        for var_name, var_data in old_settings.items():
            if var_name in context_var_node["variables"].keys():
                var_plug = context_var_node["variables"][var_name]
                for key, value in var_data.items():
                    var_plug[key].setValue(value)

    def collect_submission_settings(self, instance):
        """
        Construct a dictionary of the default (selected) submission settings.
        That means, pool, secondary pool, group, priority, submit suspended
        and limits.

        """

        # this stuff is gathered from the plugin `collect_deadline_pools`
        primary_pool = instance.data.get("primaryPool", "none")
        secondary_pool = instance.data.get("secondaryPool", "none")
        group = instance.data.get("group", "")
        priority = instance.data["attributeValues"].get(
                "priority", self.priority)
        suspended = instance.data["attributeValues"].get("suspended", False)
        limits = ",".join(instance.data["attributeValues"]["limits"])

        return {
            "pool": primary_pool,
            "secondaryPool": secondary_pool,
            "group": group,
            "priority": priority,
            "submitSuspended": suspended,
            "limits": limits,
        }
