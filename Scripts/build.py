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
import subprocess
import datetime


def get_git_branch():
    if not os.path.exists('/usr/bin/git'):
        return 'unknown'

    cur_branch = None

    stdout = subprocess.check_output('git branch',
                                     stderr=subprocess.STDOUT,
                                     shell=True)
    lines = stdout.split('\n')
    for line in lines:
        if line.startswith('*'):
            cur_branch = line.replace('* ', '')
            break

    if not cur_branch:
        return 'unknown'

    if cur_branch == 'master':
        return 'master'

    command = 'git --no-pager log --graph --oneline --all ' \
              '--decorate | fgrep %s' % cur_branch
    stdout = subprocess.check_output(command,
                                     stderr=subprocess.STDOUT,
                                     shell=True)

    branch = None
    lines = stdout.split('\n')
    for line in lines:
        if line.find('(') == -1:
            continue

        if line.find(cur_branch) == -1:
            continue

        lpos = line.find('(')
        rpos = line.find(')')
        branch_spec = line[lpos + 1:rpos]
        tokens = branch_spec.split(',')

        idx = 0
        while idx < len(tokens):
            branch = tokens[idx]
            if branch != 'HEAD':
                break

            idx += 1

        if not branch:
            return 'unknown'

        btokens = branch.split('/')
        if btokens[-1] == cur_branch:
            return branch.strip()

        return '%s#%s' % (branch.strip(), cur_branch)

    if not branch:
        return 'unknown'

    return branch


def set_build_number(path):
    print('### Building %s' % path)

    fp = open(path, 'r')
    lines = fp.readlines()
    fp.close()

    fp = open(path, 'w')
    for line in lines:
        if line.startswith('build_number ='):
            tokens = line.split()
            build_number = int(tokens[2])
            build_number += 1
            fp.write('build_number = %d\n' % build_number)
            continue

        if line.startswith('build_date = '):
            today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f %Z')
            fp.write('build_date = \'%s\'\n' % today)
            continue

        if line.startswith('build_branch = '):
            branch = get_git_branch()
            fp.write('build_branch = \'%s\'\n' % branch)
            continue

        fp.write(line)

    fp.close()


# change to Scripts parent directory
if os.path.dirname(__file__).endswith('Scripts'):
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))

set_build_number('Driver/hlm-cp')

output = subprocess.check_output('python Scripts/install.py',
                                 stderr=subprocess.STDOUT,
                                 shell=True)
print(output)
