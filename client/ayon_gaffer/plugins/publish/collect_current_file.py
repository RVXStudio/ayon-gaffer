import pyblish.api

from openpype.lib import get_version_from_path
from openpype.hosts.gaffer.api import get_root


class CollectCurrentScriptGaffer(pyblish.api.ContextPlugin):
    """Collect current Gaffer script"""

    order = pyblish.api.CollectorOrder - 0.4
    label = "Collect Current Script"
    hosts = ["gaffer"]

    def process(self, context):
        """Collect all image sequence tools"""

        script = get_root()
        assert script, "Must have active Gaffer script"
        context.data["currentScript"] = script
        self.log.info(f"Collected currentScript:[{script}],")

        # Store path to current file
        filepath = script["fileName"].getValue()
        context.data['currentFile'] = filepath
        self.log.info(f"Collected currentFile:[{filepath}],")

        # store the version
        context.data["version"] = get_version_from_path(filepath)
        self.log.info(f"Collected version:[{context.data['version']}],")


