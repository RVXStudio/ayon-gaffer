import pyblish.api
import os
import ayon_core.lib


class CollectGafferFarmCleanup(pyblish.api.ContextPlugin):
    """Collect extra directories to remove on the farm"""

    order = pyblish.api.CollectorOrder + 0.49999
    label = "Collect Gaffer farm cleanup"
    targets = ["farm"]

    # TODO: this could most definetly be settings-controlled
    folder_patterns = ["{stagingDir}/aovs"]

    def process(self, context):
        """Collect extra folders to clean up"""

        if context.data["hostName"] != "gaffer":
            self.log.debug("This isn't gaffer. Not doing anything here.")
            return

        staging_dirs = set()

        if not context.data.get("stagingDir_persistent"):
            staging_dir = context.data.get("stagingDir")
            if staging_dir is not None:
                staging_dirs.add(staging_dir)

        for instance in context:
            if not instance.data.get("stagingDir_persistent"):
                staging_dir = instance.data.get("stagingDir")
                if staging_dir is not None:
                    staging_dirs.add(staging_dir)

        self.log.info(f"Found staging dirs {staging_dirs}")
        if context.data.get("cleanupFullPaths") is None:
            context.data["cleanupFullPaths"] = []

        for staging_dir in staging_dirs:
            for pattern in self.folder_patterns:
                pattern_template = ayon_core.lib.StringTemplate(pattern)
                tdata = {"stagingDir": staging_dir}
                try:
                    extra_folder = pattern_template.format_strict(tdata)
                except Exception as err:
                    self.log.warning(f"Could not format [{pattern}]: {err}")
                    continue

                if not os.path.exists(extra_folder):
                    self.log.warning(f"Can't find folder [{extra_folder}]")
                    continue

                self.log.info(
                    f"Adding folder to cleanupFullPaths: [{extra_folder}]")
                context.data["cleanupFullPaths"].append(extra_folder)
