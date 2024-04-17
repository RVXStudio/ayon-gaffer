import os
import re
import json
import getpass
from datetime import datetime

import requests
import pyblish.api


from ayon_core.pipeline.publish import (
    AyonPyblishPluginMixin
)

from ayon_core.lib import (
    BoolDef,
    NumberDef,
    Logger
)

import GafferDeadline
import Gaffer
import GafferDispatch

import ayon_gaffer.api.lib

log = Logger.get_logger("ayon_gaffer.plugins.publish.submit_gaffer_render_deadline")


class GafferSubmitDeadline(pyblish.api.InstancePlugin,
                           AyonPyblishPluginMixin):
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
    group = "skjoldur"
    pool = "main"
    department = ""
    limit_groups = {}
    use_gpu = False
    env_allowed_keys = []
    env_search_replace_values = {}
    workfile_dependency = True

    env_vars_to_submit = {
        "ARNOLD_ROOT": "",
        "AYON_RENDER_JOB": "1",
        "FTRACK_API_KEY": "",
        "FTRACK_API_USER": "",
        "FTRACK_SERVER": "",
        "OPENPYPE_SG_USER": "",
        "AVALON_PROJECT": "",
        "AVALON_ASSET": "",
        "AVALON_TASK": "",
        "AVALON_APP_NAME": "",
        "AYON_BUNDLE_NAME": "",
        "DEADLINE_ENVIRONMENT_CACHE_DIR": "",
    }

    deadline_attrs = {
        "group": group,
        "pool": pool
    }

    @classmethod
    def get_attribute_defs(cls):
        return [
            NumberDef(
                "priority",
                label="Priority",
                default=cls.priority,
                decimals=0
            ),
            NumberDef(
                "chunk",
                label="Frames Per Task",
                default=cls.chunk_size,
                decimals=0,
                minimum=1,
                maximum=1000
            ),
            NumberDef(
                "concurrency",
                label="Concurrency",
                default=cls.concurrent_tasks,
                decimals=0,
                minimum=1,
                maximum=10
            ),
            BoolDef(
                "use_gpu",
                default=cls.use_gpu,
                label="Use GPU"
            ),
            BoolDef(
                "suspend_publish",
                default=False,
                label="Suspend publish"
            ),
            BoolDef(
                "workfile_dependency",
                default=True,
                label="Workfile Dependency"
            )
        ]

    def process(self, instance):
        if not instance.data.get("farm"):
            self.log.debug("Skipping local instance.")
            return
        instance.data["attributeValues"] = self.get_attr_values_from_data(
            instance.data)

        # add suspend_publish attributeValue to instance data
        instance.data["suspend_publish"] = instance.data["attributeValues"][
            "suspend_publish"]

        # families = instance.data["families"]
        frames = instance.data['frameList']

        # set the publish priority to follow the given priority
        instance.data["priority"] = instance.data["attributeValues"].get(
            "priority", self.priority)

        node = instance.data["transientData"]["node"]
        # context = instance.context
        self.log.info(f"Submitting {node}")
        with node.scriptNode().context() as ctxt:
            render_shot_name = instance.data["asset"].split("/")[-1]
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
            saved_settings = self.apply_submission_settings(node, instance)

            saved_context_vars = self.set_render_context_vars(node, render_shot_name)

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

    def apply_submission_settings(self, root_node, instance):
        self.log.info(
            f"Applying submission settings for"
            f"[{root_node.getName()}]"
        )

        saved_values = {}
        for node in root_node.children(GafferDispatch.TaskNode):
            log.info(f" ** {node.getName()} **")
            deadline_settings = node['dispatcher']['deadline']
            current_settings = {}
            for sett in deadline_settings.children():
                if sett.typeName() == 'Gaffer::CompoundDataPlug':
                    continue
                current_settings[sett.getName()] = sett.getValue()
            saved_values[node.getName()] = current_settings

            for key, value in self.deadline_attrs.items():
                deadline_settings[key].setValue(value)

            # set priority
            priority = instance.data["attributeValues"].get("priority", self.priority)
            deadline_settings["priority"].setValue(priority)
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
