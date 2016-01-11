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
import sys
import shutil
import subprocess

import inventory


def main(args):
    top = os.path.join(os.path.dirname(__file__), '..')
    os.chdir(top)

    verbose = True if len(args) > 0 and args[0] == '-v' else False

    top = os.getcwd()
    k_cp_build = os.path.join(top, 'ConfigurationProcessor')
    k_cp_build = os.path.join(k_cp_build, 'build')
    k_cp_build = os.path.join(k_cp_build, 'lib')
    k_cp_build = os.path.join(k_cp_build, 'helion_configurationprocessor')

    return_value = True

    num_pass = 0
    num_fail = 0

    for mp in inventory.getModulePaths():
        name = inventory.getModuleName(mp)
        if name and name.find('helion') != -1:
            os.chdir(mp)

            cur_build = os.path.join('.', 'build')
            cur_build = os.path.join(cur_build, 'lib')
            cur_build = os.path.join(cur_build,
                                     'helion_configurationprocessor')

            if name != 'helion_configurationprocessor':
                if os.path.exists(cur_build):
                    shutil.rmtree(cur_build)
                shutil.copytree(k_cp_build, cur_build)

            cur_test = os.path.join('.', 'build')
            cur_test = os.path.join(cur_test, 'lib')
            cur_test = os.path.join(cur_test, name)
            cur_test = os.path.join(cur_test, 'cp')
            cur_test = os.path.join(cur_test, 'controller')
            cur_test = os.path.join(cur_test, 'test')
            if os.path.exists(cur_test):
                shutil.rmtree(cur_test)

            if os.path.exists('tox.ini'):
                print('@@@ Running tests in %s...' % mp),

                result, errors = _run_tox()

                if result:
                    print('[pass]')
                    num_pass += 1
                else:
                    print('[fail - %d error%s]' % (len(errors),
                                                   '' if len(errors) == 1 else
                                                   's'))
                    if verbose:
                        for e in errors:
                            print('----> %s' % e)
                        print('\n')

                    num_fail += 1
                    return_value = False

            os.chdir(top)

    num_test = num_pass + num_fail
    avg = float(num_pass) / float(num_test) * 100.0
    print('### %.0f%% Passing' % avg)

    return return_value


def _run_tox():

    command = ['tox']
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    out, err = p.communicate()

    errors = []

    for line in out.split('\n'):
        if line.find('congratulations') != -1:
            return True, 0

        if line.find(': E') != -1:
            errors.append(line)

        elif line.find(': W') != -1:
            errors.append(line)

        elif line.startswith('E '):
            errors.append(line)

    return False, errors

if __name__ == '__main__':
    if main(sys.argv[1:]):
        sys.exit(0)

    sys.exit(-1)
