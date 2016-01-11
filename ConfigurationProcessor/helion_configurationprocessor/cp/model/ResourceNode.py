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

from helion_configurationprocessor.cp.model.CPState import CPState
from helion_configurationprocessor.cp.model.NodeRole import NodeRole

from helion_configurationprocessor.cp.controller.NetworkConfigController \
    import NetworkConfigController


class ResourceNode(object):
    @staticmethod
    def is_active(elem_cp, node_type, rn):
        if isinstance(rn, int):
            rn_id = int(rn)
        else:
            rn_id = ResourceNode.id_from_hostname(rn)

        resource_nodes = elem_cp.get('resource-nodes', dict())
        for rn, elem_rn in six.iteritems(resource_nodes):
            if rn.lower() != node_type.lower():
                continue

            states = elem_rn.get('states', dict())
            for s, elem_s in six.iteritems(states):
                if int(s) != rn_id:
                    continue

                state = elem_s.get('state', 'active')
                return CPState.is_active(state)

        return True

    @staticmethod
    def get_active_count(elem_cp, node_type):
        resource_nodes = elem_cp.get('resource-nodes', dict())
        for rn, elem_rn in six.iteritems(resource_nodes):
            if rn.lower() != node_type.lower():
                continue

            count = elem_rn.get('count', 0)
            states = elem_rn.get('states', dict())
            for s, elem_s in six.iteritems(states):
                state = elem_s.get('state', 'active')
                if not CPState.is_active(state):
                    count -= 1

            return count

        return 0

    @staticmethod
    def get_control_plane_id(hostname):
        host_enc = NetworkConfigController.decode_hostname(hostname)
        return host_enc['control-plane-ref']

    @staticmethod
    def get_type(hostname):
        host_enc = NetworkConfigController.decode_hostname(hostname)
        return host_enc['node-type']

    @staticmethod
    def id_from_hostname(hostname):
        host_enc = NetworkConfigController.decode_hostname(hostname)
        node_id = host_enc['node-id']
        return int(node_id.replace('N', ''))

    @staticmethod
    def equals_ignoring_traffic_group(hostname1, hostname2):
        host_enc1 = NetworkConfigController.decode_hostname(hostname1)
        host_enc2 = NetworkConfigController.decode_hostname(hostname2)

        if host_enc1['host-type'] != host_enc2['host-type']:
            return False

        if host_enc1['cloud-nickname'] != host_enc2['cloud-nickname']:
            return False

        if host_enc1['control-plane-ref'] != host_enc2['control-plane-ref']:
            return False

        if host_enc1['node-type'] != host_enc2['node-type']:
            return False

        if host_enc1['node-id'] != host_enc2['node-id']:
            return False

        return True

    @staticmethod
    def is_resource_node(hostname):
        host_enc = NetworkConfigController.decode_hostname(hostname)
        host_type = host_enc['host-type']

        resource_node = NodeRole.to_type(NodeRole.RESOURCE_NODE)

        return host_type == resource_node

    @staticmethod
    def get_hostname(elem_rn):
        pass

    @staticmethod
    def get_services(elem_rn):
        return elem_rn.get('services', [])

    @staticmethod
    def is_service_present(svc_controller, elem_rn, service_name):
        for elem_s in elem_rn.get('services', []):
            if svc_controller.equals(elem_s, service_name):
                return True

        return False

    @staticmethod
    def is_any_service_present(svc_controller, elem_rn, service_names):
        for sn in service_names:
            if ResourceNode.is_service_present(svc_controller, elem_rn, sn):
                return True

        return False
