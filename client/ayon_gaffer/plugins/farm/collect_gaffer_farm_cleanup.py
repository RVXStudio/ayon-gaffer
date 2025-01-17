import pyblish.api
import os
import ayon_core.lib

class CollectGafferFarmCleanup(pyblish.api.ContextPlugin):
    """Collect extra directories to remove on the farm"""

    order = pyblish.api.CollectorOrder + 0.4
    label = "Collect Gaffer farm cleanup"
    hosts = ["gaffer"]
    targets = ["farm"]

    folder_patterns = ["{stagingDir}/aovs"]

    def process(self, context):
        """Collect extra folders to clean up"""

        self.log.info(f"STARTING FARM COLlECTING")

        staging_dirs = []

        if not context.data.get("stagingDir_persistent"):
            staging_dirs.extend(context.data.get("stagingDir", []))

        for instance in context:
            if not instance.data.get("stagingDir_persistent"):
                staging_dirs.extend(instance.data.get("stagingDir", []))


        if context.data.get("cleanupFullPaths") is None:
            context.data["cleanupFullPaths"] = []

        for staging_dir in staging_dirs:
            for pattern in folder_patterns:
                pattern_template = StringTemplate(pattern)
                tdata = {"stagingDir": staging_dir}
                try:
                    extra_folder = pattern_template.format_strict(tdata)
                except Exception as err:
                    self.log.warning(f"Could not format [{pattern}]: {err}")
                    continue

                if not os.path.exists(extra_folder):
                    self.log.warning(f"Can't find folder [{extra_folder}]")
                    continue

                self.log.info(f"Adding folder to cleanupFullPaths: [{extra_folder}]")
                context.data["cleanupFullPaths"].append(extra_folder)
