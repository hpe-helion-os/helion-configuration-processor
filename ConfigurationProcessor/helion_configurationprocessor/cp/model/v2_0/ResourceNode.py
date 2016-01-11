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


class ResourceNode(object):
    @staticmethod
    def count(elem_rn):
        return elem_rn.get('count', 0)

    @staticmethod
    def name(elem_rn):
        return elem_rn.get('name', '')

    @staticmethod
    def failure_zone(elem_rn):
        return elem_rn.get('failure-zone', 'default')

    @staticmethod
    def server_role(elem_rn):
        return elem_rn.get('role', '')

    @staticmethod
    def servers(elem_rn):
        return elem_rn.get('servers', dict())
