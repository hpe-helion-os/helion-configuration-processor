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
from helion_configurationprocessor.cp.model.ControlPlane import ControlPlane
from helion_configurationprocessor.cp.model.CloudModel import CloudModel
from helion_configurationprocessor.cp.model.ResourceNode import ResourceNode

from helion_configurationprocessor.cp.model.StatePersistor \
    import StatePersistor


class Server(object):
    @staticmethod
    def is_active(cloud_model, elem_s):
        if isinstance(elem_s, dict):
            if 'state' in elem_s:
                state = elem_s.get('state', CPState.ACTIVE)
                return CPState.is_active(state)

            if Server.is_allocated(elem_s):
                name = Server.hostname(elem_s)
                if ResourceNode.is_resource_node(name):
                    return Server.is_resource_node_active(cloud_model, name)

        elif ResourceNode.is_resource_node(elem_s):
            return Server.is_resource_node_active(cloud_model, elem_s)

        return True

    @staticmethod
    def is_deleted(models, controllers, elem_s):
        state_persistor = StatePersistor(
            models, controllers,
            persistence_file='server_allocations.yml')

        info = state_persistor.recall_info()
        for k, v in six.iteritems(info):
            if (v['pxe-mac-addr'] != elem_s['pxe-mac-addr'] or
                    v['pxe-ip-addr'] != elem_s['pxe-ip-addr']):
                continue

            if 'state' not in v:
                return False

            if not CPState.is_active(v['state']):
                return True

            return False

        return False

    @staticmethod
    def is_resource_node_active(cloud_model, elem_s):
        control_planes = CloudModel.control_planes(cloud_model)

        control_plane = ResourceNode.get_control_plane_id(elem_s)
        node_type = ResourceNode.get_type(elem_s)
        for elem_cp in control_planes:
            cp_name = ControlPlane.get_name(elem_cp)

            if cp_name.lower() != control_plane.lower():
                continue

            if not ResourceNode.is_active(elem_cp, node_type, elem_s):
                return False

        return True

    @staticmethod
    def is_allocated(elem_s):
        elem_a = elem_s.get('allocations', dict())
        return 'hostname' in elem_a

    @staticmethod
    def allocations(elem_s):
        return elem_s.get('allocations', dict())

    @staticmethod
    def hostname(elem_s):
        elem_a = elem_s.get('allocations', dict())
        return elem_a.get('hostname', None)

    @staticmethod
    def tags(elem_s):
        return elem_s.get('tags', None)
