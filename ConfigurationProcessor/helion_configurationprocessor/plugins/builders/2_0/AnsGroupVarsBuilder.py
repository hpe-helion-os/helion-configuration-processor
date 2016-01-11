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

from copy import deepcopy
from helion_configurationprocessor.cp.model.v2_0.HlmPaths \
    import HlmPaths
from helion_configurationprocessor.cp.model.v2_0.CloudDescription \
    import CloudDescription
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel

from helion_configurationprocessor.cp.model.BuilderPlugin \
    import BuilderPlugin
from helion_configurationprocessor.cp.model.BuilderPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog
from helion_configurationprocessor.cp.model.v2_0.HlmVariable \
    import HlmVariable


LOG = logging.getLogger(__name__)


class AnsGroupVarsBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(AnsGroupVarsBuilder, self).__init__(
            2.0, instructions, models, controllers,
            'ans-group-vars-2.0')
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

        cloud_name = CloudDescription.get_cloud_name(self.cloud_desc)
        control_planes = CloudModel.get(self._cloud_internal, 'control-planes')
        components = CloudModel.get(self._cloud_internal, 'components')
        components_by_mnemonic = CloudModel.get(self._cloud_internal, 'components_by_mnemonic')

        for cp_name, cp in control_planes.iteritems():
            self._build_ansible_group_vars(cloud_name, cp, components, components_by_mnemonic)

    def _build_ansible_group_vars(self, cloud_name, cp, components, components_by_mnemonic):

        cp_group_vars = {'cp-name': cp['name']}
        cp_prefix = "%s-%s" % (cloud_name, cp['name'])
        for cluster in cp['clusters']:

            host_prefix = "%s-%s-%s" % (cloud_name, cp['name'], cluster['name'])

            self._build_service_vars(cp_group_vars, cp, cp_prefix, host_prefix,
                                     cluster['service-components'],
                                     cluster['servers'], components,
                                     components_by_mnemonic)

            group_vars = {}
            self._build_group_vars(group_vars, cp, cp_prefix, host_prefix,
                                   cluster['service-components'],
                                   cluster['servers'], components,
                                   components_by_mnemonic)

            group_vars['failure-zones'] = cluster.get('failure-zones',
                                                      cp.get('failure-zones', []))

            # Sort the service list to make it easier to compare accross changes
            group_vars['group']['services'] = \
                sorted(group_vars['group']['services'])

            # Create group vars for the cluster
            filename = "%s/group_vars/%s-%s-%s" % (
                self._file_path, cloud_name, cp['name'], cluster['name'])
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            self.add_artifact(filename, ArtifactMode.CREATED)
            with open(filename, 'w') as fp:
                yaml.dump(group_vars, fp, default_flow_style=False, indent=4)

        # Add the failure zones for this control plane
        cp_group_vars['failure_zones'] = cp.get('failure-zones', [])

        # Add the list of zone types for this control plane
        cp_group_vars['zone_types'] = {}
        for type, zones in cp.get('zone-types', {}).iteritems():
            cp_group_vars['zone_types'][type] = []
            for zone in sorted(zones):
                cp_group_vars['zone_types'][type].append(zone)

        # Add the list of verb hosts for this control plane
        cp_group_vars['verb_hosts'] = {}
        for component_name in cp['components']:
            component = components[component_name]
            name = component['mnemonic'].replace('-', '_')
            cp_group_vars['verb_hosts'][name] = "%s-%s" % (component['mnemonic'],
                                                           cp['name'])

        # Add the list of network tag values for this control plane
        cp_group_vars['network_tag_values'] = self._build_network_tag_values(cp)

        # Create the control plane group vars
        filename = "%s/group_vars/%s-%s" % (
            self._file_path, cloud_name, cp['name'])
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        self.add_artifact(filename, ArtifactMode.CREATED)
        with open(filename, 'w') as fp:
            yaml.dump(cp_group_vars, fp, default_flow_style=False, indent=4)

        if 'resources' in cp:
            for res_name, resources in cp['resources'].iteritems():

                group_vars = {}
                component_list = []
                for c in resources['service-components']:
                    if c not in cp.get('common-service-components', []):
                        component_list.append(c)

                host_prefix = "%s-%s-%s" % (cloud_name, cp['name'], res_name)
                self._build_service_vars(group_vars, cp, cp_prefix, host_prefix,
                                         component_list,
                                         resources['servers'], components,
                                         components_by_mnemonic)

                self._build_group_vars(group_vars, cp, cp_prefix, host_prefix,
                                       resources['service-components'],
                                       resources['servers'], components,
                                       components_by_mnemonic)

                group_vars['failure-zones'] = resources.get('failure-zones',
                                                            cp.get('failure-zones', []))

                # Sort the service list to make it easier to compare accross changes
                group_vars['group']['services'] = \
                    sorted(group_vars['group']['services'])

                filename = "%s/group_vars/%s-%s-%s" % (
                    self._file_path, cloud_name, cp['name'], res_name)
                if not os.path.exists(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))
                self.add_artifact(filename, ArtifactMode.CREATED)

                with open(filename, 'w') as fp:
                    yaml.dump(group_vars, fp, default_flow_style=False, indent=4)

    def _build_service_vars(self, group_vars, cp, cp_prefix, cluster_prefix,
                            component_list, cluster_servers, components,
                            components_by_mnemonic):

        for component_name in component_list:
            if component_name in cp['components']:

                component = components[component_name]
                name = component['mnemonic'].replace('-', '_')
                group_vars[name] = {}
                component_group_vars = group_vars[name]

                # Add endpoints for this component
                if component_name in cp['advertises']:
                    vips = cp['advertises'].get(component_name, {})
                    advertises = {'vips': {}}
                    for keystone_data in ['keystone-service-name',
                                          'keystone-service-type']:
                        if keystone_data in component:
                            # NOTE(kuvaja): As Ansible does not allow '-'
                            # character in the variable names, we need to
                            # twiggle around a bit here.
                            advertises[keystone_data.replace('-', '_')] = \
                                component[keystone_data]

                    component_group_vars['advertises'] = advertises
                    for role in ['admin', 'internal', 'public']:
                        if role in vips:
                            for region in cp['region-list']:
                                vip = {'host': vips[role]['hostname'],
                                       'ip_address': vips[role]['ip_address'],
                                       'port': vips[role]['port'],
                                       'protocol': vips[role]['protocol'],
                                       'url': vips[role]['url'],
                                       'region_name': region}
                                if role == 'internal':
                                    role_name = 'private'
                                else:
                                    role_name = role

                                if role_name not in advertises['vips']:
                                    advertises['vips'][role_name] = []
                                advertises['vips'][role_name].append(vip)

                # Add the details of all components we consume
                component_group_vars.update(cp['components'][component_name].get('consumes', {}))

                # Add members if advertised.  Note that CP1.0 does this
                # on a specific network, but we just have one internal
                # endpoint for each component
                if 'advertise-member-list-on' in component:
                    member_data = cp['members'][component_name]
                    component_group_vars['members'] = {}
                    for role, ports in member_data['ports'].iteritems():

                        if role == 'internal':
                            role_name = 'private'
                        else:
                            role_name = role

                        component_group_vars['members'][role_name] = []
                        members = component_group_vars['members'][role_name]
                        for port in ports:
                            for host_data in member_data['hosts']:
                                members.append({'host': host_data['hostname'],
                                                'member_id': host_data['member_id'],
                                                'port': port})

                    # TODO: Remove once all playbooks have switched to using
                    #      internal vip for mysql and rabbit
                    # Hack needed to keep compatiblity with 1.0
                    # which declared an internal endpoint as public
                    if components[component_name].get(
                            'publish-internal-as-public', False):
                        component_group_vars['members']['public'] = \
                            deepcopy(component_group_vars['members']['private'])

                # Add details of any component we provide a proxy for
                lb_components = cp['load-balancers'].get(component_name, {})
                for lb_component_name, lb_data in lb_components.iteritems():
                    if 'has_proxy' not in component_group_vars:
                        component_group_vars['has_proxy'] = {}
                    proxied_component = components[lb_component_name]['mnemonic'].replace('-', '_')
                    component_group_vars['has_proxy'][proxied_component] = {
                        'networks': [],
                        'servers': [],
                        'initiate_tls': lb_data['host-tls'],
                        'vars': {}}
                    for host_data in lb_data['hosts']:
                        component_group_vars['has_proxy'][proxied_component]['servers'].append(
                            host_data['hostname'])

                    for net_data in lb_data['networks']:
                        proxy_data = {'ports': [net_data['vip-port']],
                                      'server_ports': [net_data['host-port']],
                                      'vip': net_data['hostname'],
                                      'ip_address': net_data['ip-address'],
                                      'terminate_tls': net_data['vip-tls']}

                        if 'vip-options' in net_data:
                            proxy_data['vip_options'] = net_data['vip-options']

                        if 'vip-check' in net_data:
                            proxy_data['vip_check'] = net_data['vip-check']

                        if 'vip-backup-mode' in net_data:
                            proxy_data['vip_backup_mode'] = net_data['vip-backup-mode']

                        if 'cert-file' in net_data:
                            proxy_data['cert_file'] = net_data['cert-file']

                        component_group_vars['has_proxy'][proxied_component]['networks'].append(proxy_data)

                # Add details of contained services
                for contains_name, contains_data in component.get('contains', {}).iteritems():
                    rel_name = "%s_has_container" % contains_data['name']
                    component_group_vars[rel_name] = {'members': {},
                                                      'vips': {}
                                                      }
                    for var in contains_data.get('relationship-vars', []):
                        if 'vars' not in component_group_vars[rel_name]:
                            component_group_vars[rel_name]['vars'] = {}
                        payload = var['properties'] if 'properties' in var else None
                        value = HlmVariable.generate_value(
                            self._instructions, self._models,
                            self._controllers, var['name'], var['value'],
                            payload=payload)
                        component_group_vars[rel_name]['vars'][var['name']] = value

                    vip_data = []
                    for net, vips in cp['vip_networks'].iteritems():
                        for vip in vips:
                            if vip['component-name'] == contains_name:
                                vip_data.append(vip)
                    for vip in vip_data:
                        for role in vip['roles']:
                            if role == 'internal':
                                role = 'private'
                            component_group_vars[rel_name]['members'][role] = []
                            component_group_vars[rel_name]['vips'][role] = []

                            for host_data in vip['hosts']:
                                component_group_vars[rel_name]['members'][role].append(
                                    {'host': host_data['hostname'],
                                     'port': vip['host-port']
                                     })

                            component_group_vars[rel_name]['vips'][role].append(
                                {'vip': vip['hostname'],
                                 'port': vip['host-port']
                                 })
                # Add Log info
                if 'produces-log-files' in component:
                    component_group_vars['produces_log_files'] = {'vars': {}}
                    component_log_info = component_group_vars['produces_log_files']

                    for log_info in component['produces-log-files']:
                        for var in log_info['relationship-vars']:
                            component_log_info['vars'][var['name']] = []
                            for val in var['value']:
                                for k, v in val.iteritems():
                                    component_log_info['vars'][var['name']].append({k: v})

                # Print out any config set - Not sure if we need this with our config
                # approach ?
                config_set = component.get('config-set', [])
                for config in config_set:
                    if 'ansible-vars' in config:
                        if 'vars' not in component_group_vars:
                            component_group_vars['vars'] = {}
                        for var in config['ansible-vars']:
                            payload = var['properties'] if 'properties' in var else None
                            value = HlmVariable.generate_value(
                                self._instructions, self._models,
                                self._controllers, var['name'], var['value'],
                                payload=payload)
                            component_group_vars['vars'][var['name']] = value

    def _build_group_vars(self, group_vars, cp, cp_prefix, cluster_prefix,
                          component_list, cluster_servers, components,
                          components_by_mnemonic):

        if 'group' not in group_vars:
            group_vars['group'] = {}

        if 'services' not in group_vars['group']:
            group_vars['group']['services'] = []

        group_vars['group']['vars'] = {'control_plane_prefix': cp_prefix,
                                       'network_address_prefix': cluster_prefix}

        for component_name in component_list:
            if component_name in components:
                component = components[component_name]
                group_vars['group']['services'].append(component['mnemonic'])
                group_vars['group']['services'].append(component_name)

    #
    # Build a list of all network tag values within a control plane
    # Tag values are keys by service (to make it easy for a playbook to find the
    # list its interestd in and network group (as the same tag/value will be on
    # multiple hosts and we want to keep them unique within the list)
    #
    def _build_network_tag_values(self, cp):

        network_tag_values = {}
        for cluster in cp['clusters']:
            self._get_network_tag_values(cluster.get('servers', []),
                                         network_tag_values)

        if 'resources' in cp:
            for res_name, resources in cp['resources'].iteritems():
                self._get_network_tag_values(resources.get('servers', []),
                                             network_tag_values)

        return network_tag_values

    #
    # Update a list of all network tag values from a list of servers
    #
    @staticmethod
    def _get_network_tag_values(servers, tag_values):

        for server in servers:
            for if_name, if_data in server['interfaces'].iteritems():
                for net_name, net_data in if_data['networks'].iteritems():
                    for tag in net_data.get('service-tags', []):
                        if tag['service'] not in tag_values:
                            tag_values[tag['service']] = {}
                        if net_data['network-group'] not in tag_values[tag['service']]:
                            tag_values[tag['service']][net_data['network-group']] = {}
                        net_group_tag_values = tag_values[tag['service']][net_data['network-group']]
                        if tag['name'] not in net_group_tag_values:
                            net_group_tag_values[tag['name']] = tag['values']

    def get_dependencies(self):
        return []
