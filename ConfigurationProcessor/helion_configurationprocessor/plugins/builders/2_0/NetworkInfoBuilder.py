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

from helion_configurationprocessor.cp.model.BuilderPlugin \
    import BuilderPlugin
from helion_configurationprocessor.cp.model.BuilderPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class NetworkInfoBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(NetworkInfoBuilder, self).__init__(
            2.0, instructions, models, controllers,
            'net-info-2.0')
        LOG.info('%s()' % KenLog.fcn())

        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions, self.cloud_desc)

        self._cloud_model = self._models['CloudModel']
        self._cloud_version = CloudModel.version(self._cloud_model, self._version)
        self._cloud_internal = CloudModel.internal(self._cloud_model)

        HlmPaths.make_path(self._file_path)

    def build(self):
        LOG.info('%s()' % KenLog.fcn())

        control_planes = CloudModel.get(self._cloud_internal, 'control-planes')

        net_info = {}

        # Service IPs
        for cp_name, cp in control_planes.iteritems():
            for cluster in cp['clusters']:
                if 'service-ips' in cluster:
                    if 'service_ips' not in net_info:
                        net_info['service_ips'] = {}

                    for name, net_data in cluster['service-ips'].iteritems():
                        if name not in net_info['service_ips']:
                            net_info['service_ips'][name] = []
                        for net_name, data in net_data.iteritems():
                            info = {'control_plane': cp_name,
                                    'cluster': cluster['name'],
                                    'network': net_name,
                                    'hosts': data.get('hosts', []),
                                    'cluster_ip': data.get('cluster-ip', {})}
                        net_info['service_ips'][name].append(info)

            if 'resources' in cp:
                for res_name, resources in cp['resources'].iteritems():
                    if 'service-ips' in resources:
                        if 'service_ips' not in net_info:
                            net_info['service_ips'] = {}

                        for name, net_data in resources['service-ips'].iteritems():
                            if name not in net_info['service_ips']:
                                net_info['service_ips'][name] = []
                            for net_name, data in net_data.iteritems():
                                info = {'control_plane': cp_name,
                                        'cluster': res_name,
                                        'network': net_name,
                                        'hosts': data.get('hosts', []),
                                        'cluster_ip': data.get('cluster-ip', {})}
                                net_info['service_ips'][name].append(info)

        filename = "%s/info/net_info.yml" % (
            self._file_path)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        self.add_artifact(filename, ArtifactMode.CREATED)

        with open(filename, 'w') as fp:
            yaml.dump(net_info, fp, default_flow_style=False, indent=4)

    def get_dependencies(self):
        return []
