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


class FirewallInfoBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(FirewallInfoBuilder, self).__init__(
            2.0, instructions, models, controllers,
            'firewall-info-2.0')
        LOG.info('%s()' % KenLog.fcn())

        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions, self.cloud_desc)

        self._cloud_model = self._models['CloudModel']
        self._cloud_version = CloudModel.version(self._cloud_model, self._version)
        self._cloud_internal = CloudModel.internal(self._cloud_model)

        HlmPaths.make_path(self._file_path)

    def build(self):
        LOG.info('%s()' % KenLog.fcn())

        firewall_settings = CloudModel.get(self._cloud_internal, 'firewall_settings')
        print (firewall_settings)
        cloud_firewall = CloudModel.get(self._cloud_internal, 'cloud-firewall')

        # Convert from per server to per network
        firewall = {}
        for server_name, data in cloud_firewall.iteritems():
            for addr, rules in data.get('rules', {}).iteritems():
                for rule in rules:
                    net_group = rule['chain']
                    component = rule['component']
                    if net_group not in firewall:
                        firewall[net_group] = {}
                    min_port = rule['port-range-min']
                    max_port = rule['port-range-max']
                    if min_port == max_port:
                        port = str(min_port)
                    else:
                        port = "%s:%s" % (min_port, max_port)

                    if port not in firewall[net_group]:
                        firewall[net_group][port] = {'port': port,
                                                     'protocol': rule['protocol'],
                                                     'components': [],
                                                     'addresses': []}
                    if component not in firewall[net_group][port]['components']:
                        firewall[net_group][port]['components'].append(component)
                    if addr not in firewall[net_group][port]['addresses']:
                        firewall[net_group][port]['addresses'].append(addr)

        # rebuild  get a list with the ports sorted
        sorted_firewall = {}
        for net_grp, data in firewall.iteritems():
            sorted_firewall[net_grp] = []
            for port in sorted(data, key=lambda x: int(x.split(":")[0])):
                sorted_firewall[net_grp].append(data[port])

        filename = "%s/info/firewall_info.yml" % (
            self._file_path)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        self.add_artifact(filename, ArtifactMode.CREATED)

        with open(filename, 'w') as fp:
            yaml.dump(sorted_firewall, fp, default_flow_style=False, indent=4)

    def get_dependencies(self):
        return ['ans-host-vars-2.0']
