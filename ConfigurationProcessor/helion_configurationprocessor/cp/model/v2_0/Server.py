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


class Server(object):
    @staticmethod
    def name(elem_s):
        return elem_s.get('name', None)

    @staticmethod
    def address(elem_s):
        return elem_s.get('addr', None)

    @staticmethod
    def components(elem_s):
        return elem_s.get('components', [])

    @staticmethod
    def services(elem_s):
        return elem_s.get('services', [])

    @staticmethod
    def num_components(elem_s):
        return len(elem_s.get('components', []))

    @staticmethod
    def num_services(elem_s):
        return len(elem_s.get('services', []))

    @staticmethod
    def interfaces(elem_s):
        return elem_s.get('interfaces', dict())

    @staticmethod
    def routes(elem_s):
        return elem_s.get('routes', dict())

    @staticmethod
    def num_routes(elem_s):
        return len(elem_s.get('routes', []))
