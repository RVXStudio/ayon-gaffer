import json
import pyblish.api


class IntegrateSaveGafferCleanupFile(pyblish.api.InstancePlugin):
    """Collect current Gaffer script"""

    order = pyblish.api.IntegratorOrder + 0.35
    label = "Integrate save gaffer cleanup file"
    hosts = ["gaffer"]
    families = ["render"]

    def process(self, instance):
        cleanup_file_path = instance.data.get("gaffer_cleanup_file_path")

        if cleanup_file_path is None:
            self.log.info(f"No gaffer cleanup file path, nothing to do ...")
            return

        cleanup_paths = instance.data.get("gaffer_cleanup_paths")
        if cleanup_paths is None:
            self.log.info(f"No cleanup paths, that's strange.")
            return

        with open(cleanup_file_path, "wt") as cleanfile:
            json.dump(cleanup_paths, cleanfile)
            self.log.info(f"Saved file [{cleanup_file_path}]")
