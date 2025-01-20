import pyblish.api
import os
import json


class CollectGafferFarmCleanup(pyblish.api.ContextPlugin):
    """Collect extra directories to remove on the farm"""

    order = pyblish.api.CollectorOrder + 0.49999
    label = "Collect Gaffer farm cleanup"
    targets = ["farm"]

    def process(self, context):
        """Collect extra folders to clean up"""

        if context.data["hostName"] != "gaffer":
            self.log.debug("This isn't gaffer. Not doing anything here.")
            return

        if context.data.get("cleanupFullPaths") is None:
            context.data["cleanupFullPaths"] = []

        for instance in context:
            staging_dir = instance.data["stagingDir"]
            gaffer_cleanup_file = os.path.join(
                staging_dir, "gaffer_cleanup.json")
            if not os.path.exists(gaffer_cleanup_file):
                self.log.info(f"No cleanup file at [{gaffer_cleanup_file}]!")
                return
            with open(gaffer_cleanup_file, "rt") as cleanfile:
                cleanup_paths = json.load(cleanfile)
                for cleanup_path in cleanup_paths:
                    self.log.info(
                        f"Adding path to cleanupFullPaths: [{cleanup_path}]")
                    context.data["cleanupFullPaths"].append(cleanup_path)
