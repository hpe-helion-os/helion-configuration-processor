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

from .utils import read_json, read_yaml
from .json_diff import compare_json


def _map_in_situ(l, fn):
    for i, v in enumerate(l):
        l[i] = fn(v)


def _sort_in_situ(l, key):
    l.sort(key=lambda v: v.get(key))


def _sanitise(loader):
    def _sanitise(fn):
        def _preprocess(d1, d2, file):
            """Specialise a JSON comparison"""

            j1 = loader(d1, file)
            j2 = loader(d2, file)

            try:
                fn(j1)
            except KeyError:
                pass
            try:
                fn(j2)
            except KeyError:
                pass

            return compare_json(j1, j2)
        return _preprocess
    return _sanitise


@_sanitise(read_json)
def cloudmodel_json(j):
    """There are some known instabilities in the output here"""

    j['cloud-date'] = u'Tue May 19 13:51:28 2015'
    _map_in_situ(j['command-line'], os.path.basename)
    _sort_in_situ(j['ip-addresses'], 'index')
    _sort_in_situ(j['service-components'], 'mnemonic')


@_sanitise(read_yaml)
def group_vars_all(j):
    print "In group_vars_all"
    for k, l in j['global']['service_connections'].iteritems():
        _sort_in_situ(l, 'network')
