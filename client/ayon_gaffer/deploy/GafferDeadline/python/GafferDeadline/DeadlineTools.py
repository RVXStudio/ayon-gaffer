##########################################################################
#
#  Copyright (c) 2019, Hypothetical Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of Hypothetical Inc. nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import os
import subprocess
import re
import json

import IECore

try:
    from ayon_core.settings import get_project_settings
    from ayon_core.pipeline import registered_host
    from ayon_deadline.abstract_submit_deadline import requests_post
    AYON_MODE = True
except Exception as err:
    print("Could not import ayon_core stuff", err)
    AYON_MODE = False
    raise RuntimeError(f"Could not import ayon modules.")


DEADLINE_SETTINGS = None


def needs_ayon_settings(func):
    '''This decorator makes sure tht the DEADLINE_SETTINGS variable is set to
    the correct value when running tool functions.

    '''

    def ayon_settings_check(self, *args, **kwargs):
        if DEADLINE_SETTINGS is None:
            fetch_ayon_settings()
        return func(self, *args, **kwargs)

    return ayon_settings_check


def fetch_ayon_settings():
    global DEADLINE_SETTINGS
    host = registered_host()
    ayon_settings = get_project_settings(
        host.get_current_project_name())
    try:
        DEADLINE_SETTINGS = ayon_settings["deadline"]
    except KeyError:
        print(f"NO deadline settings found!")


def runDeadlineCommand(arguments, hideWindow=True):
    if "DEADLINE_PATH" not in os.environ:
        raise RuntimeError(
            "DEADLINE_PATH must be set to the Deadline executable path")
    executableSuffix = ".exe" if os.name == "nt" else ""
    deadlineCommand = os.path.join(
        os.environ['DEADLINE_PATH'],
        "deadlinecommand" + executableSuffix
    )

    arguments = [deadlineCommand] + arguments

    p = subprocess.Popen(
        arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, err = p.communicate()

    if err:
        raise RuntimeError(
            "Error running Deadline command {}: {}".format(
                " ".join(arguments),
                output
            )
        )

    return output


@needs_ayon_settings
def submitJob(payload):
    ws_settings = DEADLINE_SETTINGS["deadline_urls"][0]
    auth = (ws_settings["default_username"],
            ws_settings["default_password"])
    verify = not ws_settings["not_verify_ssl"]
    deadline_url = "{}/api/jobs".format(ws_settings["value"])
    response = requests_post(deadline_url,
                             json=payload,
                             timeout=10,
                             auth=auth,
                             verify=verify)

    if not response.ok:
        return (None, response.json())

    results = response.json()
    return (results["_id"], results)


def getMachineList():
    output = runDeadlineCommand(["GetSlaveNames"])
    return [i.decode() for i in output.split()]


def getLimitGroups():
    output = runDeadlineCommand(["GetLimitGroups"])
    return re.findall(r'Name=(.*)', output.decode())


def getGroups():
    output = runDeadlineCommand(["GetSubmissionInfo", "groups"])
    return [i.decode() for i in output.split()[1:]]    # remove [Groups] header


def getPools():
    output = runDeadlineCommand(["GetSubmissionInfo", "pools"])
    return [i.decode() for i in output.split()[1:]]    # remove [Groups] header
