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


class Network(object):
    @staticmethod
    def name(elem_n):
        return elem_n.get('name', None)

    @staticmethod
    def addr(elem_n):
        return elem_n.get('addr', None)

    @staticmethod
    def cidr(elem_n):
        return elem_n.get('cidr', None)

    @staticmethod
    def hostname(elem_n):
        return elem_n.get('hostname', None)
