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
import six

from helion_configurationprocessor.cp.model.Member import Member
from helion_configurationprocessor.cp.model.CPState import CPState
from helion_configurationprocessor.cp.model.NodeTypes import NodeTypes


class Tier(object):
    @staticmethod
    def get(elem_cp, t_id):
        t_name = t_id.replace('T', '')
        for elem_t in elem_cp['tiers']:
            if Tier.equals(elem_t, t_name):
                return elem_t

        return None

    @staticmethod
    def get_name(elem_t):
        return '%s' % int(elem_t['id'])

    @staticmethod
    def is_active(elem_t):
        state = elem_t.get('state', None)
        if state:
            return CPState.is_active(state)

        return len(elem_t['services']) > 0

    @staticmethod
    def is_active_or_empty(elem_t):
        state = elem_t.get('state', None)
        if state:
            return CPState.is_active(state)

        return True

    @staticmethod
    def is_member_active(elem_t, member_id):
        if 'member-states' not in elem_t:
            return True

        for ms, elem_ms in six.iteritems(elem_t['member-states']):
            if Member.normalize(ms) == Member.normalize(member_id):
                state = elem_ms.get('state', CPState.ACTIVE)
                return CPState.is_active(state)

        return True

    @staticmethod
    def equals(elem_t, tid):
        return int(elem_t['id']) == int(tid)

    @staticmethod
    def get_active_member_count(elem_t):
        mc = elem_t.get('member-count', 1)

        if 'member-states' not in elem_t:
            return mc

        for ms, elem_ms in six.iteritems(elem_t['member-states']):
            state = elem_ms.get('state', CPState.ACTIVE)
            if not CPState.is_active(state):
                mc -= 1

        return mc

    @staticmethod
    def get_controller_nodes(elem_t):
        return elem_t.get('controller-nodes', [])

    @staticmethod
    def get_controller_node_services(elem_t):
        return elem_t.get('controller-node-services', [])

    @staticmethod
    def get_node_type(elem_t):
        nt = elem_t['node-type']
        type_name = NodeTypes.get_name(nt)
        return type_name

    @staticmethod
    def get_members(elem_t):
        return six.iteritems(elem_t['members'])

    @staticmethod
    def get_dependent_nodes(elem_t):
        return elem_t.get('dependent-nodes', [])

    @staticmethod
    def get_dependent_nodes_count(elem_t):
        nodes = elem_t.get('dependent-nodes', [])
        return len(nodes)

    @staticmethod
    def get_virtual_machines(elem_t):
        return elem_t.get('virtual-machines', [])

    @staticmethod
    def get_virtual_machine_count(elem_t):
        nodes = elem_t.get('virtual-machines', [])
        return len(nodes)

    @staticmethod
    def is_service_present(svc_controller, elem_t, service_name):
        for elem_s in elem_t.get('services', []):
            if svc_controller.equals(elem_s['name'], service_name):
                return True

        return False

    @staticmethod
    def is_any_service_present(svc_controller, elem_t, service_names):
        for sn in service_names:
            if Tier.is_service_present(svc_controller, elem_t, sn):
                return True

        return False
