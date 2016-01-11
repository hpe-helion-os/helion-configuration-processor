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
import os
import logging
import logging.config
import yaml

from helion_configurationprocessor.cp.model.v2_0.HlmPaths \
    import HlmPaths
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel
from helion_configurationprocessor.cp.model.v2_0.CloudDescription \
    import CloudDescription
from helion_configurationprocessor.cp.model.v2_0 \
    import ServerState

from helion_configurationprocessor.cp.model.BuilderPlugin \
    import BuilderPlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog
from helion_configurationprocessor.cp.model.BuilderPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.lib.DataTransformer \
    import DataTransformer

LOG = logging.getLogger(__name__)


class AnsibleAllVarsBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(AnsibleAllVarsBuilder, self).__init__(
            2.0, instructions, models, controllers,
            'ansible-all-vars-2.0')
        LOG.info('%s()' % KenLog.fcn())
        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions, self.cloud_desc)
        self._file_path = os.path.join(self._file_path, 'ansible')

        self._cloud_model = self._models['CloudModel']
        self._cloud_version = CloudModel.version(self._cloud_model, self._version)
        self._cloud_internal = CloudModel.internal(self._cloud_model)

        HlmPaths.make_path(self._file_path)

    def build(self):
        LOG.info('%s()' % KenLog.fcn())

        filename = "%s/group_vars/all" % (self._file_path)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        self.add_artifact(filename, ArtifactMode.CREATED)

        global_vars = {'global': {'ansible_vars': [],
                                  'all_servers': []}}
        control_planes = CloudModel.get(self._cloud_internal, 'control-planes')
        service_view = CloudModel.get(self._cloud_internal, 'service_view')
        service_view = service_view['by_region']
        servers = CloudModel.get(self._cloud_internal, 'servers')
        ring_specifications = CloudModel.get(self._cloud_internal,
                                             'ring-specifications', [])
        pass_through = CloudModel.get(self._cloud_internal, 'pass_through')
        cloud_name = CloudDescription.get_cloud_name(self.cloud_desc)
        ntp_servers = self.cloud_desc['ntp-servers']

        if ntp_servers:
            global_vars['global']['ntp_servers'] = ntp_servers

        #
        # Add a list of all vips
        #
        vips = set()
        for cp_name, cp in control_planes.iteritems():
            for ep_name, ep_data in cp['endpoints'].iteritems():
                for role, role_data in ep_data.iteritems():
                    if role not in ['internal', 'admin']:
                        continue
                    for data in role_data:
                        access = data.get('access', {})
                        if 'hostname' in access:
                            vips.add(data['access']['hostname'])
                        for host_data in access.get('members', []):
                            vips.add(host_data['hostname'])

        if ring_specifications:
            ring_specifications = DataTransformer(
                ring_specifications).all_output('-', '_')
            global_vars['global']['all_ring_specifications'] =\
                ring_specifications
        else:
            global_vars['global']['all_ring_specifications'] = []

        if pass_through:
            global_vars['global']['pass_through'] = pass_through['global']

        global_vars['global']['vips'] = sorted(vips)

        global_vars['topology'] = {'cloud_name': cloud_name,
                                   'control_planes': []}
        for cp_name in sorted(service_view):
            cp = service_view[cp_name]
            cp_data = {'name': cp_name,
                       'services': []}
            for service_name in sorted(cp):
                components = cp[service_name]
                service_data = {'name': service_name,
                                'components': []}

                for component_name in sorted(components):
                    hosts = components[component_name]
                    component_data = {'name': component_name,
                                      'hosts': sorted(hosts)}
                    service_data['components'].append(component_data)

                cp_data['services'].append(service_data)

            global_vars['topology']['control_planes'].append(cp_data)

        #
        # Include disk details of all servers for Swift
        #
        for server in servers:
            if server['state'] == ServerState.ALLOCATED:
                disk_model_out = DataTransformer(
                    server['disk-model']).all_output('-', '_')
                server_info = {'name': server['hostname'],
                               'rack': server.get('rack', None),
                               'region': server.get('region', None),
                               'disk_model': disk_model_out}
                global_vars['global']['all_servers'].append(server_info)

                network_names = []
                for if_name, if_data in server['interfaces'].iteritems():
                    for net_name, net_data in if_data['networks'].iteritems():
                        if 'hostname' in net_data:
                            network_names.append(net_data['hostname'])
                server_info['network_names'] = network_names

        with open(filename, 'w') as fp:
            yaml.dump(global_vars, fp, default_flow_style=False, indent=4)

    def get_dependencies(self):
        return []
