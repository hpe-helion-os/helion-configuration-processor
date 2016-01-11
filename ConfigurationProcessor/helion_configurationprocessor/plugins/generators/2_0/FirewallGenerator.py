# (c) Copyright 2015 Hewlett Packard Enterprise Development Company #
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import logging
import logging.config

from helion_configurationprocessor.cp.model.CPLogging import \
    CPLogging as KenLog
from helion_configurationprocessor.cp.model.GeneratorPlugin \
    import GeneratorPlugin
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel


LOG = logging.getLogger(__name__)


class FirewallGenerator(GeneratorPlugin):
    def __init__(self, instructions, models, controllers):
        super(FirewallGenerator, self).__init__(
            2.0, instructions, models, controllers,
            'firewall-generator-2.0')
        LOG.info('%s()' % KenLog.fcn())

    def generate(self):
        LOG.info('%s()' % KenLog.fcn())

        self._generate_firewall_rules()

    def _generate_firewall_rules(self):
        LOG.info('%s()' % KenLog.fcn())
        self._action = KenLog.fcn()
        cloud_version = CloudModel.version(
            self._models['CloudModel'], self._version)
        cloud_internal = CloudModel.internal(self._models['CloudModel'])

        firewall_rules = CloudModel.get(cloud_version, 'firewall-rules', [])
        network_groups = CloudModel.get(cloud_version, 'network-groups')
        components = CloudModel.get(cloud_internal, 'components', [])

        # If component is not set then it means an earlier generator failed
        if not components:
            return

        # Initialise the firewall structure
        net_group_firewall = {}
        for net_group in network_groups:
            net_group_firewall[net_group['name']] = {'user': [],
                                                     'component': {}}

        #
        # Add ports from components.
        #
        explicit_components = set()
        for net_group in network_groups:
            for comp in self._get_netgroup_components(net_group, exclude_default=True):
                explicit_components.add(comp)

        for net_group in network_groups:
            net_group_components = self._get_netgroup_components(net_group)
            for comp_name, comp_data in components.iteritems():
                if (comp_name in net_group_components
                        or ('default' in net_group_components
                            and comp_name not in explicit_components)):
                    comp_rules = []
                    for endpoint in comp_data.get('endpoints', []):
                        if ':' in str(endpoint['port']):
                            ports = str.split(endpoint['port'], ':')
                        else:
                            ports = [endpoint['port'], endpoint['port']]
                        rule = {'type': 'allow',
                                'remote-ip-prefix': '0.0.0.0/0',
                                'port-range-min': ports[0],
                                'port-range-max': ports[1],
                                'protocol': endpoint.get('protocol', 'tcp')}

                        comp_rules.append(rule)

                    if comp_rules:
                        net_group_firewall[net_group['name']]['component'][comp_name] = comp_rules

        # Annotate the rules so we can trace where they came from
        for rule_group in firewall_rules:
            for rule in rule_group.get('rules', []):
                rule['component'] = "user-%s" % rule_group['name']

        #
        # Add user defined rules to network groups
        #
        for rule in firewall_rules:
            if rule.get('final'):
                continue
            for firewall_netgroup in rule['network-groups']:
                for net_group in network_groups:
                    if (firewall_netgroup == "all"
                            or firewall_netgroup == net_group['name']):
                        net_group_firewall[net_group['name']]['user'].extend(rule['rules'])

        #
        # Add user defined final rules to network groups
        #
        for rule in firewall_rules:
            if not rule.get('final'):
                continue
            for firewall_netgroup in rule['network-groups']:
                for net_group in network_groups:
                    if (firewall_netgroup == "all"
                            or firewall_netgroup == net_group['name']):
                        net_group_firewall[net_group['name']]['user'].extend(rule['rules'])

        CloudModel.put(cloud_internal, 'net-group-firewall', net_group_firewall)

    def _get_netgroup_components(self, net_group, exclude_default=False):
        comp_list = set()
        for comp in net_group.get('component-endpoints', []):
            comp_list.add(comp)
        for comp in net_group.get('tls-component-endpoints', []):
            comp_list.add(comp)
        if exclude_default and 'default' in comp_list:
            comp_list.remove('default')
        return comp_list

    def get_dependencies(self):
        return ['cloud-cplite-2.0']
