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

import IECore

try:
    from ayon_core.settings import get_project_settings
    from ayon_core.pipeline import registered_host
    from ayon_deadline.abstract_submit_deadline import (
        requests_post,
        requests_get
    )
    AYON_MODE = True
except Exception as err:
    print("Could not import ayon_core stuff", err)
    AYON_MODE = False
    raise RuntimeError(f"Could not import ayon modules.")


DEADLINE_SETTINGS = None


def inject_ayon_settings(func):
    '''This decorator makes sure tht the DEADLINE_SETTINGS variable is set to
    the correct value when running tool functions.

    '''

    def ayon_settings_check(*args, **kwargs):
        if DEADLINE_SETTINGS is None:
            fetch_ayon_settings()
        # now we have populated settings.
        ws_settings = DEADLINE_SETTINGS["deadline_urls"][0]
        auth = (ws_settings["default_username"],
                ws_settings["default_password"])
        verify = not ws_settings["not_verify_ssl"]
        url = ws_settings["value"]

        deadline_settings = {
            "auth": auth,
            "verify": verify,
            "url": url
        }
        return func(*args, deadline_settings, **kwargs)

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
        raise RuntimeError


@inject_ayon_settings
def submitJob(payload, dl_settings):
    deadline_url = "{}/api/jobs".format(dl_settings["url"])
    response = requests_post(deadline_url,
                             json=payload,
                             timeout=10,
                             auth=dl_settings["auth"],
                             verify=dl_settings["verify"])

    if not response.ok:
        return (None, response.json())

    results = response.json()
    return (results["_id"], results)


@inject_ayon_settings
def getMachineList(dl_settings):
    deadline_url = "{}/api/slaves".format(dl_settings["url"])
    response = requests_get(deadline_url,
                            params={"NamesOnly": True},
                            auth=dl_settings["auth"],
                            verify=dl_settings["verify"])
    if not response.ok:
        raise RuntimeError(f"Error fetching machine list {response.text}")
    return response.json()


@inject_ayon_settings
def getLimitGroups(dl_settings):
    deadline_url = "{}/api/limitgroups".format(dl_settings["url"])
    response = requests_get(deadline_url,
                            params={"NamesOnly": True},
                            auth=dl_settings["auth"],
                            verify=dl_settings["verify"])
    if not response.ok:
        raise RuntimeError(f"Error fetching machine list {response.text}")
    return response.json()


@inject_ayon_settings
def getGroups(dl_settings):
    deadline_url = "{}/api/groups".format(dl_settings["url"])
    response = requests_get(deadline_url,
                            params={"NamesOnly": True},
                            auth=dl_settings["auth"],
                            verify=dl_settings["verify"])
    if not response.ok:
        raise RuntimeError(f"Error fetching machine list {response.text}")
    return response.json()


@inject_ayon_settings
def getPools(dl_settings):
    deadline_url = "{}/api/pools".format(dl_settings["url"])
    response = requests_get(deadline_url,
                            params={"NamesOnly": True},
                            auth=dl_settings["auth"],
                            verify=dl_settings["verify"])
    if not response.ok:
        raise RuntimeError(f"Error fetching machine list {response.text}")
    return response.json()
