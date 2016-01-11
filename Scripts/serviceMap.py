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
import six
import json
import yaml
import sys

from collections import OrderedDict


def get_contents(file_name):
    try:
        fp = open(file_name, 'r')
        lines = fp.readlines()
        fp.close()
    except:
        return None

    fixed_lines = []
    for line in lines:
        if line.find('#') != -1:
            line = line[:line.find('#')]

        fixed_lines.append(line)

    try:
        if file_name.endswith('.json'):
            contents = json.loads(''.join(fixed_lines))
        elif file_name.endswith('.yml') or file_name.endswith('.yaml'):
            contents = yaml.load(''.join(fixed_lines))
        else:
            print('Cannot load file %s' % file_name)
            return None
    except:
        print('Syntax errors detected in file %s' % file_name)
        return None

    return contents


def process_services(contents, service_map):
    for elem_sc in contents['service-components']:

        if elem_sc['name'] in service_map:
            continue

        service_map[elem_sc['name']] = elem_sc['mnemonic']

    return service_map


def main(args):

    if not os.path.exists('services.json'):
        print('Must run this script from Data/Site')
        return -1

    service_map = OrderedDict()

    exts = ['json', 'yml', 'yaml']
    for ext in exts:
        contents = get_contents('services.%s' % ext)
        if contents:
            service_map = process_services(contents, service_map)

    if os.path.exists('services') and os.path.isdir('services'):
        for root, dirs, files in os.walk('services'):
            for f in files:
                file_name = os.path.join(root, f)
                contents = get_contents(file_name)
                if contents:
                    service_map = process_services(contents, service_map)

    if len(args) > 1 and args[0] == '-s':
        print('Sending output to %s' % args[1])
        fp = open(args[1], 'w')
        for name, mnemonic in six.iteritems(service_map):
            fp.write('%s::%s\n' % (name, mnemonic))
        fp.close()

    else:
        for name, mnemonic in six.iteritems(service_map):
            print('%s::%s' % (name, mnemonic))

if __name__ == "__main__":
    main(sys.argv[1:])
