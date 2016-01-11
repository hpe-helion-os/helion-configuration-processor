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
from helion_configurationprocessor.cp.model.Service import Service


class DependentNode(object):
    @staticmethod
    def get_name(elem_dn):
        if elem_dn:
            return elem_dn['name']

        return None

    @staticmethod
    def get_services(elem_dn):
        return elem_dn['services']

    @staticmethod
    def has_service(svc_controller, elem_dn, service):
        for elem_s in DependentNode.get_services(elem_dn):
            if svc_controller.equals(
                    Service.get_name(elem_s), Service.get_name(service)):
                return True

        return False

    @staticmethod
    def get_ip_address(cloud_model, hostname):
        for elem_cs in cloud_model['config-sets']:
            for elem_v in elem_cs['vars']:
                if (elem_v['group'] == hostname and
                        elem_v['name'] == 'my_network_address'):
                    return elem_v['value']

        return None
