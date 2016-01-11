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


class NodeRole(object):
    CONTROLLER_NODE = 0
    NODE_SERVICE = 1
    SERVICE_TIER = 2
    RESOURCE_NODE = 3
    RESOURCE_SERVICE_TIER = 4
    RESOURCE_CLUSTER = 5
    VIRTUAL_MACHINE = 6

    @staticmethod
    def get_roles():
        return [NodeRole.CONTROLLER_NODE, NodeRole.NODE_SERVICE,
                NodeRole.SERVICE_TIER]

    @staticmethod
    def get_roles_for_members():
        return [NodeRole.CONTROLLER_NODE, NodeRole.NODE_SERVICE,
                NodeRole.SERVICE_TIER]

    @staticmethod
    def get_roles_for_virtual_machines():
        return [NodeRole.NODE_SERVICE, NodeRole.VIRTUAL_MACHINE]

    @staticmethod
    def to_type(role):
        if role == NodeRole.CONTROLLER_NODE:
            return 'controller-nodes'
        elif role == NodeRole.NODE_SERVICE:
            return 'controller-node-services'
        elif role == NodeRole.SERVICE_TIER:
            return 'service-tiers'
        elif role == NodeRole.RESOURCE_NODE:
            return 'resource-node'
        elif role == NodeRole.RESOURCE_SERVICE_TIER:
            return 'resource-service-tier'
        elif role == NodeRole.RESOURCE_CLUSTER:
            return 'resource-cluster'
        elif role == NodeRole.VIRTUAL_MACHINE:
            return 'virtual-machines'

        return 'unknown'

    @staticmethod
    def to_node_type(nt_controller, role):
        if role == NodeRole.CONTROLLER_NODE:
            return nt_controller.get_mnemonic_by_name(
                'NODE_TYPE_CLOUD_CONTROLLER')

        elif role == NodeRole.NODE_SERVICE:
            return nt_controller.get_mnemonic_by_name(
                'NODE_TYPE_CLOUD_CONTROLLER')

        elif role == NodeRole.SERVICE_TIER:
            return nt_controller.get_mnemonic_by_name(
                'NODE_TYPE_CLOUD_CONTROLLER')

        elif role == NodeRole.VIRTUAL_MACHINE:
            return nt_controller.get_mnemonic_by_name(
                'NODE_TYPE_CLOUD_CONTROLLER')

        return 'unknown'

    @staticmethod
    def equals(role, role_type):
        return role == role_type
