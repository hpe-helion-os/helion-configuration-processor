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
from .utils import read_ini
from .comparator import EQUAL, ADDITIONAL, MISSING


def ansible_hosts(d1, d2, file):
    c1 = read_ini(d1, file)
    c2 = read_ini(d2, file)

    if c1 == c2:
        return EQUAL, None

    k1 = set(c1.keys())
    k2 = set(c2.keys())

    missing = {}
    additional = {}
    differ = {}

    for k in k1:
        if k not in k2:
            missing[k] = c1[k]
        else:
            if c1[k] != c2[k]:
                differ[k] = (c1[k], c2[k])

    if k1 - k2:
        for k in k1 - k2:
            missing[k] = c1[k]

    if k2 - k1:
        for k in k2 - k1:
            additional[k] = c2[k]

    result = ""
    ok = EQUAL
    if additional:
        ok = ADDITIONAL
        result += "\nAdditional sections: " + \
            ", ".join(sorted(additional.keys()))

    if missing:
        ok = MISSING
        result += "\nMissing sections: " + \
            ", ".join(sorted(missing.keys()))

    if differ:
        ok = ADDITIONAL
        result += "\nDiffering sections: " + \
            ", ".join(sorted(differ.keys()))

    return ok, result[1:]
