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
import json
import os
import yaml


def read_file(dir, file):
    with open(os.path.join(dir, file)) as f:
        return f.read()


def read_ini(dir, file):
    section = None
    lines = []
    result = {section: lines}

    with open(os.path.join(dir, file)) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith('['):
                section = line[1:-1]
                lines = []
                result[section] = lines
            else:
                lines.append(line)
    return result


def read_json(dir, file):
    with open(os.path.join(dir, file)) as f:
        return json.load(f)


def read_yaml(dir, file):
    with open(os.path.join(dir, file)) as f:
        return yaml.load(f)
