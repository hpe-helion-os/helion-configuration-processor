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
import difflib

import json
import json_delta

from .utils import read_json, read_yaml
from .comparator import EQUAL, DIFFER


def json_diff(d1, d2, file):
    j1 = read_json(d1, file)
    j2 = read_json(d2, file)

    return compare_json(j1, j2)


def yaml_diff(d1, d2, file):
    j1 = read_yaml(d1, file)
    j2 = read_yaml(d2, file)

    return compare_json(j1, j2)


def compare_json(j1, j2):
    diff = json_delta.diff(j1, j2, False, False)

    if not diff:
        return EQUAL, None
    else:
        try:
            return DIFFER, '\n'.join(json_delta.udiff(j1, j2, diff, 2))
        except:
            print("################ EXCEPTION ################")
            print("#                                         #")
            print("# json_delta raised an exception          #")
            print("# using fallback of difflib.unified()     #")
            print("#                                         #")
            print("###########################################")

            diff = difflib.unified_diff(
                json.dumps(j1, indent=2).split('\n'),
                json.dumps(j2, indent=2).split('\n'))
            return DIFFER, '\n'.join(diff)
