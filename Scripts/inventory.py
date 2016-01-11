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
import ast
import fnmatch
import os
import re


def getModulePaths(modulesDir='.'):
    modules = []
    for root, dirnames, filenames in os.walk(modulesDir):
        if (root.find('.tox') == -1 and root.find('.venv') == -1):
            if fnmatch.filter(filenames, 'setup.py'):
                root = re.sub(r'^\.[\/\\]', '', root)
                root = re.sub(r'\\', '/', root)
                modules.append(root)
    return modules


def getModuleName(modulePath):
    # get module name from call to setup(name=xyz) in setup.py
    name = None
    setup_py = os.path.join(modulePath, 'setup.py')
    if not os.path.isfile(setup_py):
        print(
            'Warning: File %s not found. '
            'Unable to determine module name.' % setup_py)
    else:
        with open(setup_py) as f:
            a = ast.parse(f.read())
            for op in a.body:
                if isinstance(op, ast.Expr) and \
                        isinstance(op.value, ast.Call) and \
                        isinstance(op.value.func, ast.Name) and \
                                op.value.func.id == 'setup':
                    for keyword in op.value.keywords:
                        if keyword.arg == 'name':
                            name = keyword.value.s
                            break
                    break
        if not name:
            print(
                'Warning: File %s found but unable to '
                'determine module name.' % setup_py)
    return name
