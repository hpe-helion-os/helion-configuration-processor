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
from helion_configurationprocessor.cp.model.CPState import CPState


class Member(object):
    @staticmethod
    def is_active(elem_m):
        state = elem_m.get('state', CPState.ACTIVE)
        return CPState.is_active(state)

    @staticmethod
    def equals(elem_m, mid):
        m1 = elem_m['id'].replace('M', '')
        m2 = mid.replace('M', '')

        return str(m1).lower() == str(m2).lower()

    @staticmethod
    def is_first_member(mid):
        m = mid.replace('M', '')

        return str(m) == '1'

    @staticmethod
    def normalize(mid):
        if isinstance(mid, int):
            return str(mid)

        return mid.replace('M', '')

    @staticmethod
    def get_services(elem_m):
        return elem_m.get('services', [])

    @staticmethod
    def is_vip(mid):
        if isinstance(mid, int):
            return False

        return mid.lower() == 'vip'
