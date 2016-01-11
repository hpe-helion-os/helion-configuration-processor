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


class NetworkRef(object):
    @staticmethod
    def normalize(ref):
        if ref.find(':') != -1:
            return ref.lower()

        tokens = ref.split('-')
        if len(tokens) == 3:
            return ref.replace('-', ':').lower()

        if len(tokens) == 4:
            node_type = '%s-%s' % (tokens[0], tokens[1])
            val = '%s:%s:%s' % (node_type, tokens[2], tokens[3])
            return val.lower()

        return ref
