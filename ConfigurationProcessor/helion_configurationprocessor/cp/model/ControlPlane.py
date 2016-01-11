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
from helion_configurationprocessor.cp.model.CloudModel import CloudModel
from helion_configurationprocessor.cp.model.Tier import Tier

from helion_configurationprocessor.cp.model.CPState import CPState


class ControlPlane(object):
    @staticmethod
    def get(cloud_model, cp_name):
        for elem_cp in CloudModel.control_planes(cloud_model):
            cur_name = ControlPlane.get_name(elem_cp)
            if cur_name == cp_name:
                return elem_cp

        return None

    @staticmethod
    def is_active(elem_cp):
        state = elem_cp.get('state', CPState.ACTIVE)
        return CPState.is_active(state)

    @staticmethod
    def get_name(elem_cp):
        rv = elem_cp['type'].upper()
        if rv == 'RCP':
            rv += '%02d' % int(elem_cp['id'])

        return rv

    @staticmethod
    def equals(elem_cp, cp_id):
        return ControlPlane.get_name(elem_cp) == cp_id

    @staticmethod
    def get_active_tier_count(elem_cp):
        tc = len(elem_cp['tiers'])

        for elem_t in elem_cp['tiers']:
            if not Tier.is_active(elem_t):
                tc -= 1

        return tc
