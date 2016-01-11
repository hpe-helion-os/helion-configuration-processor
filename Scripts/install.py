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
import os
import shutil
import stat
import subprocess
import sys

import inventory

VERBOSE = False


def run_setup(path):
    curdir = os.getcwd()

    print('### Installing %s' % path)
    os.chdir(path)
    if os.path.isdir('build'):
        shutil.rmtree('build')
    stdout = subprocess.check_output('%s setup.py install' % sys.executable,
                                     stderr=subprocess.STDOUT, shell=True)
    if VERBOSE:
        print(stdout)

    os.chdir(curdir)


# change to Scripts parent directory
if os.path.dirname(__file__).endswith('Scripts'):
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))

modulePaths = inventory.getModulePaths()
for modulePath in modulePaths:
    run_setup(modulePath)

cp_dest = os.path.sep + 'var'
cp_dest = os.path.join(cp_dest, 'lib')
cp_dest = os.path.join(cp_dest, 'hlm')
cp_dest = os.path.join(cp_dest, 'configuration_processor')

if not os.path.exists(cp_dest):
    os.makedirs(cp_dest)

cp_dest = os.path.join(cp_dest, 'hlm-cp')

if os.path.exists(cp_dest):
    os.remove(cp_dest)

shutil.copyfile('Driver/hlm-cp', cp_dest)

os.chmod(cp_dest,
         stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
         stat.S_IRGRP | stat.S_IXGRP |
         stat.S_IROTH | stat.S_IXOTH)
