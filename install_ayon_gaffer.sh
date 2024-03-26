#!/usr/bin/env bash

repo_root=$(dirname "$(realpath ${BASH_SOURCE[0]})")
version_command="import os;import re;version={};exec(open(os.path.join('$repo_root', 'src', 'ayon_gaffer-addon', 'version.py')).read(), version);print(re.search(r'(\d+\.\d+.\d+).*', version['__version__'])[1]);"
full_version_command="import os;import re;version={};exec(open(os.path.join('$repo_root', 'src', 'ayon_gaffer-addon', 'version.py')).read(), version);print(version['__version__']);"
version="$(python <<< ${version_command})"
full_version="$(python <<< ${full_version_command})"
addon_path=/pipeline/AstralProjection/apps/ayon/addons/gaffer_$full_version

rsync -vrlptD src/ayon_gaffer-addon/client/ayon_gaffer/ /pipeline/AstralProjection/apps/ayon/builds/gaffer_$version --exclude *.pyc --exclude __pycache__

echo Installed [/pipeline/AstralProjection/apps/ayon/builds/gaffer_$version]