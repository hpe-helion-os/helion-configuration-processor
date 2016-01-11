#!/usr/bin/python
#
# (c) Copyright 2015 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
import inventory
import re
import os
import shutil
import site


def clean_module(module_name):
    # match egg file (i.e. ^name-version)
    pattern = re.compile('^%s-[0-9]' % module_name)
    try:
        for sitepackage in site.getsitepackages():
            try:
                for file in os.listdir(sitepackage):
                    if pattern.match(file):
                        file = os.path.join(sitepackage, file)
                        print('### Removing %s' % file)
                        if os.path.isdir(file):
                            shutil.rmtree(file)
                        else:
                            os.unlink(file)

            except Exception as e:
                # On MacOS you run into weird errors traversing through all of
                # the sitepackages directories
                pass
    except Exception as e:
        pass


def clean_cur_path(module_path, name):
    build_dir = os.path.join(module_path, 'build')
    if os.path.exists(build_dir):
        print('### Removing %s' % build_dir)
        shutil.rmtree(build_dir)

    dist_dir = os.path.join(module_path, 'dist')
    if os.path.exists(dist_dir):
        print('### Removing %s' % dist_dir)
        shutil.rmtree(dist_dir)

    egg_dir = os.path.join(module_path, '%s.egg-info' % name)
    if os.path.exists(egg_dir):
        print('### Removing %s' % egg_dir)
        shutil.rmtree(egg_dir)

    tox_dir = os.path.join(module_path, '.tox')
    if os.path.exists(tox_dir):
        print('### Removing %s' % tox_dir)
        shutil.rmtree(tox_dir)


# change to Scripts parent directory
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

modulePaths = inventory.getModulePaths()
for modulePath in modulePaths:
    name = inventory.getModuleName(modulePath)
    if name:
        clean_module(name)
        clean_cur_path(modulePath, name)
