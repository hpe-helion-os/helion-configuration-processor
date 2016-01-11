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

from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel
from helion_configurationprocessor.cp.model.v2_0.ServerGroup \
    import ServerGroup

from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog
from helion_configurationprocessor.cp.model.GeneratorPlugin \
    import GeneratorPlugin

from helion_configurationprocessor.cp.model.v2_0 \
    import AllocationPolicy
from helion_configurationprocessor.cp.model.v2_0 \
    import ServerState

from helion_configurationprocessor.cp.model.StatePersistor \
    import StatePersistor

from helion_configurationprocessor.cp.model.v2_0.HlmPaths \
    import HlmPaths


from copy import deepcopy
from netaddr import IPNetwork, IPAddress

LOG = logging.getLogger(__name__)


class CloudCpLiteGenerator(GeneratorPlugin):

    def __init__(self, instructions, models, controllers):
        super(CloudCpLiteGenerator, self).__init__(
            2.0, instructions, models, controllers,
            'cloud-cplite-2.0')

        LOG.info('%s()' % KenLog.fcn())

        self._address_state_persistor = StatePersistor(
            self._models, self._controllers, 'ip_addresses.yml')

        self._server_allocation_state_persistor = StatePersistor(
            self._models, self._controllers, 'server_allocations.yml')

        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions, self.cloud_desc)
        HlmPaths.make_path(self._file_path)

        self.explaination = ""
        self.explain_level = 0
        self.explain_prefix = ""
        self.explain_uline = "=-"

    def explain_block(self, block_name, level=0):
        self.explaination += '\n' + " " * (level - 1) * 2 + block_name + '\n'
        if level < len(self.explain_uline):
            uline = self.explain_uline[level]
            self.explaination += " " * (level - 1) * 2 + uline * len(block_name) + '\n'
        self.explain_level = level
        self.explain_prefix = " " * level * 2

    def explain(self, message):
        self.explaination += self.explain_prefix + message + "\n"

    def write_explanation(self):
        filename = "%s/info/explain.txt" % (self._file_path)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        with open(filename, 'w') as fp:
            fp.write(self.explaination)

    def generate(self):
        LOG.info('%s()' % KenLog.fcn())
        self._generate_cp_lite()

    def _generate_cp_lite(self):
        LOG.info('%s()' % KenLog.fcn())
        cloud_data = self._models['CloudDescription']['cloud']
        cloud_version = CloudModel.version(self._models['CloudModel'], self._version)

        services = {}
        components = {}
        components_by_mnemonic = {}
        remove_deleted_servers = self._instructions['remove_deleted_servers']
        free_unused_addresses = self._instructions['free_unused_addresses']

        for service in CloudModel.get(cloud_version, 'services'):
            services[service['name']] = service

        for component in CloudModel.get(cloud_version, 'service-components'):
            components[component['name']] = component
            components_by_mnemonic[component['mnemonic']] = component

        # Add any aliases.
        # Note use sorted() to avoid changing the dict while iterating
        for component_name in sorted(components):
            component = components[component_name]
            for alias in component.get('aliases', []):
                if alias not in components:
                    components[alias] = component

        control_planes = {}
        network_groups = {}
        load_balancers = []
        networks = {}
        network_addresses = {}
        iface_models = {}
        disk_models = {}
        nic_mappings = {}
        server_roles = {}
        server_groups = {}
        bm_servers = []
        pass_through = {'global': {}, 'servers': {}}

        # Servers
        if 'servers' in cloud_version:
            bm_servers.extend(cloud_version['servers'])

        # Build a list of server addresses so we can
        # reserve them
        server_addresses = {}
        for s in bm_servers:
            server_addresses[s['ip-addr']] = s['id']

        # Control Planes
        for cp in CloudModel.get(cloud_version, 'control-planes'):
            control_planes[cp['name']] = dict(cp)

        # Network Groups
        for net in CloudModel.get(cloud_version, 'network-groups'):
            network_groups[net['name']] = net
            network_groups[net['name']]['networks'] = []

        # Networks
        for net in CloudModel.get(cloud_version, 'networks'):
            networks[net['name']] = net

            network_addresses[net['name']] = []
            if 'cidr' in net:
                # Find the first and last address of the cidr
                cidr_start = None
                cidr_end = None
                for ipaddr in IPNetwork(unicode(net['cidr'])).iter_hosts():
                    if not cidr_start:
                        cidr_start = ipaddr
                    cidr_end = ipaddr

                if 'start-address' in net:
                    net_start = IPAddress(net['start-address'])
                else:
                    net_start = cidr_start

                # Check end Address is valid
                if 'end-address' in net:
                    net_end = IPAddress(net['end-address'])
                else:
                    net_end = cidr_end

                for ipaddr in IPNetwork(unicode(net['cidr'])).iter_hosts():
                    addr = str(ipaddr)
                    if (addr != net.get('gateway-ip', '') and
                            ipaddr >= net_start and ipaddr <= net_end):
                        network_addresses[net['name']].append(
                            {'addr': str(addr),
                             'free': True})
                self.generate_addresses(network_addresses[net['name']],
                                        server_addresses)

        # Interface Models
        for iface in CloudModel.get(cloud_version, 'interface-models'):
            iface_models[iface['name']] = iface

        # Disk Models
        for disk_model in CloudModel.get(cloud_version, 'disk-models'):
            disk_models[disk_model['name']] = disk_model

        # NIC Mapping
        for nic_map in CloudModel.get(cloud_version, 'nic-mappings', []):
            nic_mappings[nic_map['name']] = nic_map

        # Server Roles
        for role in CloudModel.get(cloud_version, 'server-roles'):
            server_roles[role['name']] = role

        # Server Groups
        for group in CloudModel.get(cloud_version, 'server-groups', []):
            server_groups[group['name']] = group

        # Pass Through
        pt_data = CloudModel.get(cloud_version, 'pass-through', [])

        ####################################
        #
        # End of reading input data
        #
        ###################################

        # Provide compatibility for any definitions still using "member-groups"
        # instead of "clusters"
        for cp_name, cp in control_planes.iteritems():
            if 'member-groups' in cp:
                msg = ("%s: Use of 'member-groups' is deprecated, "
                       "Use 'clusters' instead." % (cp_name))
                self.log_and_add_warning(msg)
                cp['clusters'] = cp['member-groups']
                del cp['member-groups']

        # Combine pass through data which maybe in multiple
        # input files into a single dict structured by server and
        # control plane.
        for pt in pt_data:
            for key in pt.get('global', {}):
                if key in pass_through['global']:
                    msg = ("Key %s is defined more than once in global "
                           "pass-through data" % (key, ))
                    self.add_error(msg)

                pass_through['global'][key] = pt['global'][key]

            for server in pt.get('servers', []):
                if server['id'] not in pass_through['servers']:
                    pass_through['servers'][server['id']] = {}
                server_data = pass_through['servers'][server['id']]

                for key in server.get('data'):
                    if key in server_data:
                        msg = ("Key %s is defined more than once for server %s "
                               "in pass-through data" % (key, server['id']))
                        self.add_error(msg)
                    server_data[key] = server['data'][key]

        # Map service components into services:
        for service_name, service in services.iteritems():
            for resource_type, data in service['components'].iteritems():
                for name in data:
                    components[name]['service'] = service_name

        # Add proxy relationships
        for component_name, component in components.iteritems():
            for container_data in component.get('has-container', []):
                container_name = container_data['service-name']
                if container_name in components_by_mnemonic:
                    container_name = components_by_mnemonic[container_name]['name']
                if 'contains' not in components[container_name]:
                    components[container_name]['contains'] = {}
                components[container_name]['contains'][component_name] = {
                    'name': component['mnemonic'].replace('-', '_'),
                    'data': container_data
                }
                component['container-name'] = container_name

        # Check that any service enpoint specifying a port range isn't
        # a vip (code doesnlt support this at the moment !)
        # Ideally would do this in a validator, but we don't have access to
        # the component data at that stage
        for component_name, component in components.iteritems():
            for endpoint in component.get('endpoints', []):
                if endpoint.get('has-vip') and ':' in str(endpoint['port']):
                    msg = ("Component %s has an invalid port value '%s' - Can't "
                           "have a port range when has-vip is true" %
                           (component_name, endpoint['port']))
                    self.add_error(msg)

        # Check that any services exist and that any which have a container are on the
        # same cluster as the container service.  Ideally would do this in a validator, but we don't
        # have access to the component data at that stage
        for cp_name, cp in control_planes.iteritems():
            for comp_name in cp.get('common-service-components', []):
                if comp_name not in components:
                    msg = ("%s: Undefined component '%s' in common-service-components." %
                           (cp_name, comp_name))
                    self.add_error(msg)

            for cluster in cp['clusters']:
                for comp_name in cluster['service-components']:
                    if comp_name not in components:
                        msg = ("%s:%s Undefined component '%s'" %
                               (cp_name, cluster['name'], comp_name))
                        self.add_error(msg)
                        continue

                    container_name = components[comp_name].get('container-name')
                    if container_name and (container_name not in cluster['service-components'] +
                                           cp.get('common-service-components', [])):
                        msg = ("%s:%s '%s' needs '%s' in same cluster" %
                               (cp_name, cluster['name'], comp_name, container_name))
                        self.add_error(msg)

            for r in cp.get('resources', []):
                for comp_name in r['service-components']:
                    if comp_name not in components:
                        msg = ("%s:%s Undefined component '%s'" %
                               (cp_name, r['name'], comp_name))
                        self.add_error(msg)
                        continue

                    container_name = components[comp_name].get('container-name')
                    if container_name and (container_name not in r['service-components'] +
                                           cp.get('common-service-components', [])):
                        msg = ("%s:%s '%s' needs '%s' in same resource group" %
                               (cp_name, r['name'], comp_name, container_name))
                        self.add_error(msg)

        # Check that any component connections in network groups.
        # Ideally would check this in a validator, but we
        # don't have access to the services there !
        connected_components = {}
        default_components = []
        lb_components = {}
        for net_group_name, net_group in network_groups.iteritems():
            for comp_name in (net_group.get('component-endpoints', []) +
                              net_group.get('tls-component-endpoints', [])):
                if comp_name == 'default':
                    if default_components:
                        default_components.append(net_group_name)
                        msg = ("'default' specific for component-endpoints in "
                               "more than one network group: %s" %
                               (default_components))
                        self.add_error(msg)
                    else:
                        default_components.append(net_group_name)
                else:
                    if comp_name not in components:
                        msg = ("Undefined component '%s' in network group %s" %
                               (comp_name, net_group_name))
                        self.add_error(msg)
                    else:
                        if 'endpoints' in components[comp_name]:
                            if comp_name in connected_components:
                                connected_components[comp_name].append(net_group_name)
                                msg = ("%s is be connected to more than one "
                                       "network group %s." %
                                       (comp_name,
                                        connected_components[comp_name]))
                                self.add_error(msg)
                            else:
                                if comp_name not in connected_components:
                                    connected_components[comp_name] = []
                                connected_components[comp_name].append(net_group_name)

            for lb in net_group.get('load-balancers', []):
                for comp_name in (lb.get('components', []) +
                                  lb.get('tls-component', [])):
                    if comp_name != 'default' and comp_name not in components:
                        msg = ("Undefined component '%s' in load balancer %s" %
                               (comp_name, lb['name']))
                        self.add_error(msg)
                        continue

                    for role in lb.get('roles', []):
                        if role not in lb_components:
                            lb_components[role] = {}
                        if comp_name in lb_components[role]:
                            lb_components[role][comp_name].append(lb['name'])
                            if comp_name == 'default':
                                msg = ("Components specifed as 'default' for more than one "
                                       "load balancer with a role of %s: %s" %
                                       (role, lb_components[role][comp_name]))
                            else:
                                msg = ("Component %s is listed for more than one "
                                       "load balancer with a role of %s: %s" %
                                       (comp_name, role, lb_components[role][comp_name]))
                            self.add_error(msg)
                        else:
                            lb_components[role][comp_name] = [lb['name']]

        # Can't do any more if we have errors in the network groups
        if self._errors:
            return

        # Add networks into their respective network groups.
        for net_name, net in networks.iteritems():
            network_groups[net['network-group']]['networks'].append(net)

        #
        # Find which tags have been deprecated or replaced
        #
        replaced_tags = {}
        deprecated_tags = {}
        for component_name, component in components.iteritems():
            for comp_tag in component.get('network-tags', []):
                for alias in comp_tag.get('aliases', []):
                    replaced_tags[alias] = comp_tag['name']
                if 'deprecated' in comp_tag:
                    deprecated_tags[comp_tag['name']] = comp_tag['deprecated']

        #
        # Expand any network group tags to include the definition
        # from the service component.  Replace any deprecated tag names
        #
        for net_group_name, net_group in network_groups.iteritems():
            tags = []
            for raw_tag in net_group.get('tags', []):
                # Convert any network group tags that are just a string to a dict
                # so that we have a consistent type
                if isinstance(raw_tag, basestring):
                    orig_tag_name = raw_tag
                    new_tag_name = replaced_tags.get(orig_tag_name, orig_tag_name)
                    tag = {new_tag_name: None}
                elif isinstance(raw_tag, dict):
                    orig_tag_name = raw_tag.keys()[0]
                    new_tag_name = replaced_tags.get(orig_tag_name, orig_tag_name)
                    tag = {new_tag_name: raw_tag[orig_tag_name]}
                else:
                    msg = ("tag %s on net group %s is an invalid format" %
                           (raw_tag, net_group_name))
                    self.add_error(msg)
                    continue

                if new_tag_name != orig_tag_name:
                    msg = ("Network tag '%s' (used on %s) is a deprecated and should be "
                           "replaced with '%s'.  Please update your input model." %
                           (orig_tag_name, net_group_name, new_tag_name))
                    self.add_warning(msg)
                elif orig_tag_name in deprecated_tags:
                    msg = ("Network tag '%s' (used on %s) is a deprecated: %s "
                           "Please update your input model." %
                           (orig_tag_name, net_group_name, deprecated_tags[orig_tag_name]))
                    self.add_warning(msg)

                # Expand into a list of all components that have this tag
                for tag_name, tag_value in tag.iteritems():
                    for component_name, component in components.iteritems():
                        for comp_tag in component.get('network-tags', []):
                            if comp_tag['name'] == tag_name:
                                tag_definition = comp_tag

                                needs_value = tag_definition.get('needs-value', False)
                                if needs_value and not tag_value:
                                    msg = ("Warning: Missing value on tag %s in "
                                           "network group %s" %
                                           (tag_name, net_group_name))
                                    self.add_error(msg)
                                    continue

                                tag_data = {
                                    'name': tag_name,
                                    'values': tag_value,
                                    'definition': tag_definition,
                                    'component': component_name,
                                    'service': components[component_name
                                                          ].get('service', 'foundation')
                                }
                                tags.append(tag_data)

            net_group['tags'] = tags

        # Load Balancers
        for netgroup_name, netgroup in network_groups.iteritems():
            for lb in netgroup.get('load-balancers', []):
                lb['network-group'] = netgroup_name
                load_balancers.append(lb)

        # Create a default interface-model for any roles that don't define one
        default_net_iface = [{'name': 'default_iface',
                              'network-groups': [x for x in network_groups],
                              'ports': ['ethX']}]

        # Create a deafult server group to hold any networks and servers not
        # specificially assigned
        default_server_group = {}

        # Fix up relationships between server groups
        for group_name, group in server_groups.iteritems():
            for child in ServerGroup.server_groups(group):
                ServerGroup.add_group(group, server_groups[child])

        # Map networks to net_groups in server groups
        networks_in_a_group = set()
        for group_name, group in server_groups.iteritems():
            for net in ServerGroup.networks(group):
                ServerGroup.add_network(group, net, networks[net]['network-group'])
                networks_in_a_group.add(net)

        # Add any unassinged networks to the default server group
        for net_name, net in networks.iteritems():
            if net_name not in networks_in_a_group:
                if server_groups:
                    self.add_warning("Network %s is not listed in a server "
                                     "group." % (net_name))
                ServerGroup.add_network(default_server_group, net_name,
                                        net['network-group'])

        # Establish the min and max size of each cluster and resource group
        for cp_name, cp in control_planes.iteritems():
            for cluster in cp.get('clusters', []):
                if 'member-count' in cluster:
                    cluster['min-count'] = cluster['member-count']
                    cluster['max-count'] = cluster['member-count']
                else:
                    cluster['min-count'] = cluster.get('min-count', 1)

            for rgroup in cp.get('resources', []):
                if 'member-count' in rgroup:
                    rgroup['min-count'] = rgroup['member-count']
                    rgroup['max-count'] = rgroup['member-count']
                else:
                    rgroup['min-count'] = rgroup.get('min-count', 0)

        # Get the persisted server data.  Take a copy so we don't update
        # the persisted state by accident
        persisted_allocations = \
            deepcopy(self._server_allocation_state_persistor.recall_info())

        # Keep track of previously allocated servers by cp, cluster, and member_id
        server_allocations = {}

        # Create a list of servers with the network details for each resolved
        servers = []
        server_ids = []
        for s in bm_servers:

            server_role = server_roles[s['role']]

            # resolve the networking

            # Find the interface model, and take a copy of the interfaces, as we may only use part of the model
            # If there is no interface-model in the server role then all networks map to the existing NIC
            if 'interface-model' in server_role:
                iface_model = iface_models[server_role['interface-model']]
                server_interfaces = deepcopy(iface_model['network-interfaces'])
            else:
                server_interfaces = deepcopy(default_net_iface)

            # Find the disk model, and take a copy of the interfaces, as we may only use part of the model
            if 'disk-model' in server_role:
                disk_model = deepcopy(disk_models[server_role['disk-model']])
            else:
                disk_model = {'drives': {}}

            # Translate network groups to the specific networks for this server
            # Note:  At this stage we have all possible networks groups defined
            #        by the interface model.  We will reduce that to just those
            #        needed once we have assinged the server to a particular role
            for iface in server_interfaces:
                iface['networks'] = {}
                iface_net_groups = (iface.get('network-groups', []) +
                                    iface.get('forced-network-groups', []))
                for net_group in iface_net_groups:
                    # Find network in the group for this server
                    if 'server-group' in s:
                        server_group = server_groups[s['server-group']]
                    else:
                        server_group = None
                    net_name = ServerGroup.find_network(server_group, net_group,
                                                        default_server_group)
                    if net_name:
                        network = networks[net_name]
                        iface['networks'][network['name']] = deepcopy(network)
                        if net_group in iface.get('forced-network-groups', []):
                            iface['networks'][network['name']]['forced'] = True
                        else:
                            iface['networks'][network['name']]['forced'] = False

            server = {'id': s['id'],
                      'role': s['role'],
                      'rack': s.get('rack'),
                      'addr': s['ip-addr'],
                      'if-model': server_role.get('interface-model', 'default'),
                      'disk-model': disk_model,
                      'interfaces': server_interfaces,
                      'nic_map': nic_mappings.get(s.get('nic-mapping', 'none')),
                      'state': None}
            servers.append(server)
            server_ids.append(s['id'])

            # Add servers to ServerGroups
            if 'server-group' in s:
                ServerGroup.add_server(server_groups[s['server-group']], server)
            else:
                # If there are server groups defined it would be odd to have
                # a server which isn't a member of a group
                if server_groups:
                    self.add_warning("Server %s is not a member of a server "
                                     "group." % (s['ip-addr']))
                ServerGroup.add_server(default_server_group, server)

            # If this server was allocated in a previous run keep it as the
            # same member_id in the same cluster.
            # If the server has been deleted at some stage then it can return
            # provided the cluster limit isn't exceeded
            if s['id'] not in persisted_allocations:
                server['state'] = ServerState.AVAILABLE
            else:
                alloc = persisted_allocations[s['id']]
                if 'cp_name' not in alloc:
                    server['state'] = ServerState.AVAILABLE
                elif alloc['state'] == ServerState.DELETED and remove_deleted_servers:
                    server['state'] = ServerState.AVAILABLE
                    self._server_allocation_state_persistor.delete_info([s['id']])
                else:
                    server['state'] = alloc['state']
                    # Track where it is / was used
                    cp_name = alloc['cp_name']
                    if alloc['type'] == 'cluster':
                        group_name = alloc['cluster_name']
                    else:
                        group_name = alloc['resource_name']
                    member_id = alloc['member_id']

                    if cp_name not in server_allocations:
                        server_allocations[cp_name] = {}
                    if group_name not in server_allocations[cp_name]:
                        server_allocations[cp_name][group_name] = \
                            {'member_ids': set(),
                             ServerState.ALLOCATED: [],
                             ServerState.DELETED: []}

                    alloc['server'] = server
                    server_allocations[cp_name][group_name][alloc['state']].append(alloc)
                    server_allocations[cp_name][group_name]['member_ids'].add(member_id)

        # Check if we have any persisted allocations for a group that no longer
        # exists in the model.

        # Build a map of the type for each group so we can report it any error message
        persisted_group_type = {}
        for id, data in persisted_allocations.iteritems():
            group_type = data.get('type')
            if group_type == 'cluster':
                persisted_group_type[data['cluster_name']] = group_type
            elif group_type == 'resource':
                persisted_group_type[data['resource_name']] = group_type

        for cp_name, cp in control_planes.iteritems():
            current_groups = set()
            for cluster in cp['clusters']:
                current_groups.add(cluster['name'])
            for r in cp.get('resources', []):
                current_groups.add(r['name'])

            for group_name in server_allocations.get(cp_name, []):
                if group_name not in current_groups:
                    msg = ("Cluster deleted from input model\n"
                           "Persisted server allocations found for %s "
                           "'%s' that no longer exists in control plane %s. " %
                           (persisted_group_type.get(group_name, ''), group_name, cp_name))
                    for alloc_data in server_allocations[cp_name][group_name]['allocated']:
                        msg += ("\n         member:%s server:%s (%s)" %
                                (alloc_data['member_id'],
                                 alloc_data['server']['id'], alloc_data['server']['addr']))
                    msg += ("\n    If these servers are no longer used they must be "
                            "removed from the input model.")
                    self.add_error(msg)

        # Mark any servers which are in persisted state but not the list of servers
        # as deleted.  Keep the information about where they were used in the state
        # for now, and show the member id is used unless we've been given the
        # remove_deleted_servers option on the command line
        deleted_msg = ""
        for id, info in persisted_allocations.iteritems():
            if id not in server_ids:
                if remove_deleted_servers:
                    self._server_allocation_state_persistor.delete_info([id])
                else:
                    # Still track that we had a server in a particular slot so
                    # we don't reallocate that identity
                    if 'cp_name' in info:
                        cp_name = info['cp_name']
                        if info['type'] == 'cluster':
                            group_name = info['cluster_name']
                        else:
                            group_name = info['resource_name']
                        member_id = info['member_id']

                        # Recored that the member_id is still associated with
                        # a server we have persisted data for, so it doesn't
                        # get reused.
                        if cp_name not in server_allocations:
                            server_allocations[cp_name] = {}
                        if group_name not in server_allocations[cp_name]:
                            server_allocations[cp_name][group_name] = \
                                {'member_ids': set(),
                                 ServerState.ALLOCATED: [],
                                 ServerState.DELETED: []}
                        server_allocations[cp_name][group_name]['member_ids'].add(member_id)
                        deleted_msg += ("\n         %s (control plane:%s cluster:%s member:%s)" %
                                        (id, cp_name, group_name, member_id))

                        info['state'] = ServerState.DELETED
                        self._server_allocation_state_persistor.persist_info({id: info})

        if deleted_msg:
            msg = ("Servers deleted from input model\n"
                   "The following server allocations are persisted but not used: "
                   "%s\n"
                   "    To free these allocations rerun the config processor with "
                   "'--remove_deleted_servers'" % deleted_msg)
            self.add_warning(msg)

        #
        # Fix up parents
        #
        for cp_name, cp in control_planes.iteritems():
            cp['region-list'] = []
            if 'region-name' in cp:
                cp['region-list'].append(cp['region-name'])

            if 'parent' in cp:
                cp['parent-cp'] = control_planes[cp['parent']]

        # Add child region names to parent
        for cp_name, cp in control_planes.iteritems():
            if 'parent' in cp:
                if 'region-name' in cp:
                    cp['parent-cp']['region-list'].append(cp['region-name'])

        # Add common service components to all Control Planes
        for cp_name, cp in control_planes.iteritems():
            for cluster in cp['clusters']:
                cluster['service-components'].extend(cp.get('common-service-components', []))

            for r in cp.get('resources', []):
                r['service-components'].extend(cp.get('common-service-components', []))

        # Check and staisfy any depenedncies in the control plane
        for cp_name, cp in control_planes.iteritems():
            self._add_required_services_to_cp(cp, components)

        # Roles for a cluster/resource can be either a string or a list, so change to
        # always be a list
        for cp_name, cp in control_planes.iteritems():
            for cluster in cp['clusters']:
                if isinstance(cluster['server-role'], basestring):
                    cluster['server-role'] = [cluster['server-role']]

            for r in cp.get('resources', []):
                if isinstance(r['server-role'], basestring):
                    r['server-role'] = [r['server-role']]

        # Add a list of all services to each Control Plane
        for cp_name, cp in control_planes.iteritems():
            for cluster in cp['clusters']:
                cluster['services'] = {}
                for comp_name in cluster['service-components']:
                    service_name = components[comp_name].get('service', 'foundation')
                    if service_name not in cluster['services']:
                        cluster['services'][service_name] = []
                    cluster['services'][service_name].append(comp_name)

            for r in cp.get('resources', []):
                r['services'] = {}
                for comp_name in r['service-components']:
                    service_name = components[comp_name].get('service', 'foundation')
                    if service_name not in r['services']:
                        r['services'][service_name] = []
                    r['services'][service_name].append(comp_name)

        # Intialise the list of zone types.  This is where we keep track of zones for
        # those services that declare they are interested (nova, cinder, swift, etc)
        for cp_name, cp in control_planes.iteritems():
            cp['zone-types'] = {}

        # Walk through the Control Planes Allocating servers
        for cp_name in sorted(control_planes):
            self.explain_block("Allocate Servers for control plane %s" % cp_name)
            cp = control_planes[cp_name]

            hostname_data = cloud_data.get('hostname-data',
                                           {'host-prefix': cloud_data['name'],
                                            'member-prefix': '-m'})
            cp['hostname-data'] = hostname_data
            cp_allocations = server_allocations.get(cp_name, {})

            for cluster in cp['clusters']:
                self.explain_block("cluster: %s" % cluster['name'], level=1)

                # List of zones comes from the CP or the cluster
                failure_zones = cluster.get('failure-zones',
                                            cp.get('failure-zones', []))

                # Get the list of groups that are our failure zones
                failure_zone_groups = []
                for zone_name in failure_zones:
                    failure_zone_groups.append(server_groups[zone_name])

                # Update the list of per service zones in this control plane
                self._update_cp_zones(cp, failure_zones,
                                      cluster['service-components'],
                                      components)

                # Get the allocation policy
                policy = cluster.get('allocation-policy',
                                     AllocationPolicy.STRICT)

                cluster['servers'] = []
                allocations = cp_allocations.get(cluster['name'], {})
                allocated_zones = set()

                # Restore the existing Allocations
                for alloc in allocations.get(ServerState.ALLOCATED, []):
                    server = alloc['server']
                    zone = ServerGroup.get_zone(failure_zone_groups,
                                                server['id'])
                    if zone:
                        allocated_zones.add(zone)
                    elif failure_zones:
                        msg = ("Allocated server %s in cluster %s:%s is not "
                               "in the specified failure zones: %s" %
                               (server['id'], cp_name, cluster['name'],
                                failure_zones))
                        self.add_warning(msg)

                    self.explain("Persisted allocation for server '%s' (%s)" %
                                 (server['id'], zone))
                    self._add_server_to_cluster(server,
                                                alloc['member_id'], zone,
                                                cp, cluster, hostname_data)

                # Check if we're over the maximum size
                if ('max-count' in cluster
                        and len(cluster['servers']) > cluster['max-count']):
                    msg = ("Due to existing allocations %s:%s contains %s servers "
                           "which is now more that the max value specified of %s." %
                           (cp['name'], cluster['name'], len(cluster['servers']),
                            cluster['max-count']))
                    self.add_warning(msg)

                # Restore any servers that were deleted but are now back with us
                for alloc in allocations.get(ServerState.DELETED, []):
                    if ('max-count' in cluster
                            and len(cluster['servers']) >= cluster['max-count']):
                        msg = ("Cannot restore server %s as member %s of %s:%s as it "
                               "would exceed the max count of %d" %
                               (alloc['server']['id'], alloc['member_id'],
                                cp_name, cluster['name'], cluster['max-count']))
                        self.add_warning(msg)
                        continue
                    else:
                        server = alloc['server']
                        zone = ServerGroup.get_zone(failure_zone_groups,
                                                    server['id'])

                        if not zone and failure_zones:
                            msg = ("Previously deleted server %s in cluster %s:%s "
                                   "can not be restored as it is not "
                                   "in the specified failure zones: %s" %
                                   (server['id'], cp_name, cluster['name'],
                                    failure_zones))
                            self.add_warning(msg)
                        else:
                            if zone:
                                allocated_zones.add(zone)

                            self.explain("Persisted allocation for previously "
                                         "deleted server '%s' (%s)" % (server['id'], zone))
                            self._add_server_to_cluster(alloc['server'],
                                                        alloc['member_id'], zone,
                                                        cp, cluster, hostname_data)
                            msg = ("Previously deleted server restored\n"
                                   "Server '%s' has been restored to cluster %s:%s" %
                                   (alloc['server']['id'], cp_name, cluster['name']))
                            self.add_warning(msg)

                # Build a list of all the failure zones to allocate from
                search_zones = set(failure_zones)

                # If using the strict allocation policy excluding
                # any zones we already have servers from
                if policy == AllocationPolicy.STRICT:
                    for zone in allocated_zones:
                        search_zones.remove(zone)

                    # If the list of search zones is empty then we may already have
                    # servers from each zone so reset the list
                    if not search_zones:
                        search_zones = set(failure_zones)

                # Allocate any servers required to bring us up to the required
                # count
                member_id = 0
                while True:
                    if ('max-count' in cluster
                            and len(cluster['servers']) >= cluster['max-count']):
                        break

                    # Don't use member IDs that belong to current or deleted servers
                    member_id += 1
                    while member_id in allocations.get('member_ids', set()):
                        member_id += 1

                    # Build the list of zones to search
                    from_zones = []
                    for zone_name in search_zones:
                        from_zones.append(server_groups[zone_name])

                    # Find a free server for the required role
                    s = None
                    self.explain("Searching for server with role %s in zones: %s" %
                                 (cluster['server-role'], search_zones))
                    s, zone_name = ServerGroup.get_server(from_zones,
                                                          state=ServerState.AVAILABLE,
                                                          roles=cluster['server-role'],
                                                          default=default_server_group)

                    if s:
                        self.explain("Allocated server '%s' (%s)" %
                                     (s['id'], zone_name))
                        self._add_server_to_cluster(s, member_id, zone_name,
                                                    cp, cluster, hostname_data)

                        if policy == AllocationPolicy.STRICT:
                            # Remove the zone this server came from the search list
                            if zone_name:
                                search_zones.remove(zone_name)

                            # If the list is now empty then reset it
                            if not search_zones:
                                search_zones = set(failure_zones)

                    else:
                        if ('min-count' in cluster
                                and len(cluster['servers']) < cluster['min-count']):
                            msg = ("Couldn't allocate %d servers with role %s for "
                                   "cluster %s in %s" %
                                   (cluster['min-count'], cluster['server-role'],
                                    cluster['name'], cp_name))
                            if search_zones:
                                msg += " from zones %s" % (search_zones)
                            self.add_error(msg)
                        break

                # Save the state of all allocated servers
                for s in cluster['servers']:
                    state = {s['id']: {'state': s['state'],
                                       'type': 'cluster',
                                       'cp_name': cp['name'],
                                       'cluster_name': cluster['name'],
                                       'member_id': s['member_id']}}
                    self._server_allocation_state_persistor.persist_info(state)

            #
            # Now do the same thing for resource nodes
            #
            if 'resources' in cp:

                # Convert the list to a dict so we can reference it by name
                resource_nodes = {}
                for r in cp['resources']:
                    resource_nodes[r['name']] = r
                cp['resources'] = resource_nodes

                for r_name, resources in cp['resources'].iteritems():
                    self.explain_block("resource: %s" % r_name, level=1)

                    # List of zones comes from the CP or the resource group
                    failure_zones = resources.get('failure-zones',
                                                  cp.get('failure-zones', []))

                    # Get the list of groups that are our failure zones
                    failure_zone_groups = []
                    for zone_name in failure_zones:
                        failure_zone_groups.append(server_groups[zone_name])

                    # Get the allocation policy.  Default policy for a
                    # resource group is any  - this is one of the few
                    # differences between a cluster and a reosurce group
                    policy = resources.get('allocation-policy',
                                           AllocationPolicy.ANY)

                    # Update the list of per service zones in this control plane
                    self._update_cp_zones(cp, failure_zones,
                                          resources['service-components'],
                                          components)

                    resources['servers'] = []
                    allocations = cp_allocations.get(r_name, {})
                    allocated_zones = set()

                    # Restore the existing Allocations
                    for alloc in allocations.get(ServerState.ALLOCATED, []):
                        server = alloc['server']
                        zone = ServerGroup.get_zone(failure_zone_groups,
                                                    server['id'])
                        if zone:
                            allocated_zones.add(zone)
                        elif failure_zones:
                            msg = ("Allocated server %s in resource group %s:%s is not "
                                   "in the specified failure zones: %s" %
                                   (server['id'], cp_name, r_name,
                                    failure_zones))
                            self.add_warning(msg)

                        self.explain("Persisted allocation for server '%s' (%s)" %
                                     (server['id'], zone))
                        self._add_server_to_resources(alloc['server'],
                                                      alloc['member_id'], zone,
                                                      cp, resources, hostname_data)

                    # Check if we're over the maximum size
                    if ('max-count' in resources
                            and len(resources['servers']) > resources['max-count']):
                        msg = ("Due to existing allocations %s:%s contains %s servers "
                               "which is now more that the max value specified of %s." %
                               (cp['name'], r_name, len(resources['servers']),
                                resources['max-count']))
                        self.add_warning(msg)

                    # Restore any servers that were deleted but are now back with us
                    for alloc in allocations.get(ServerState.DELETED, []):
                        if ('max-count' in resources
                                and len(resources['servers']) >= resources['max-count']):
                            msg = ("Cannot restore server %s to %s:%s as it "
                                   "would exceed the max count of %d" %
                                   (alloc['server']['id'], cp_name, r_name,
                                    resources['max-count']))
                            self.add_warning(msg)
                            continue
                        else:
                            server = alloc['server']
                            zone = ServerGroup.get_zone(failure_zone_groups,
                                                        server['id'])
                            if not zone and failure_zones:
                                msg = ("Previously deleted server %s in resource group %s:%s "
                                       "can not be restored as it is not "
                                       "in the specified failure zones: %s" %
                                       (server['id'], cp_name, r_name,
                                        failure_zones))
                                self.add_error(msg)
                            else:
                                if zone:
                                    allocated_zones.add(zone)

                                self.explain("Persisted allocation for previously "
                                             "deleted server '%s' (%s)" % (server['id'], zone))

                                self._add_server_to_resources(alloc['server'],
                                                              alloc['member_id'],
                                                              zone,
                                                              cp, resources, hostname_data)

                                msg = ("Previously deleted server restored\n"
                                       "Server '%s' has been restored to resource group %s:%s" %
                                       (alloc['server']['id'], cp_name, r_name))
                                self.add_warning(msg)

                    # Build a list of all the failure zones to allocate from,
                    search_zones = set(failure_zones)

                    # If using the strict allocation policy excluding
                    # any zones we already have servers from
                    if policy == AllocationPolicy.STRICT:
                        for zone in allocated_zones:
                            search_zones.remove(zone)

                        # If the list of search zones is empty then we may already have
                        # servers from each zone so reset the list
                        if not search_zones:
                            search_zones = set(failure_zones)

                    # Allocate any servers required to bring us up to the required
                    # count
                    member_id = 0
                    while True:
                        if ('max-count' in resources
                                and len(resources['servers']) >= resources['max-count']):
                            break

                        # Don't use member IDs that belong to current or deleted servers
                        member_id += 1
                        while member_id in allocations.get('member_ids', set()):
                            member_id += 1

                        # Build the list of zones to search
                        from_zones = []
                        for zone_name in search_zones:
                            from_zones.append(server_groups[zone_name])

                        # Find a free server for the required role
                        s = None
                        self.explain("Searching for server with role %s in zones: %s" %
                                     (resources['server-role'], search_zones))
                        s, zone_name = ServerGroup.get_server(from_zones,
                                                              state=ServerState.AVAILABLE,
                                                              roles=resources['server-role'],
                                                              default=default_server_group)

                        if s:
                            self.explain("Allocated server '%s' (%s)" %
                                         (s['id'], zone_name))
                            self._add_server_to_resources(s, member_id, zone_name,
                                                          cp, resources, hostname_data)

                            if policy == AllocationPolicy.STRICT:
                                # Remove the zone this server came from the search list
                                if zone_name:
                                    search_zones.remove(zone_name)

                                # If the list is now empty then reset it
                                if not search_zones:
                                    search_zones = set(failure_zones)

                        else:
                            if ('min-count' in resources
                                    and len(resources['servers']) < resources['min-count']):
                                msg = ("Couldn't allocate %d servers with role %s for "
                                       "resource group %s in %s" %
                                       (resources['min-count'], resources['server-role'],
                                        r_name, cp_name))
                                if search_zones:
                                    msg += " from zones %s" % (search_zones)
                                self.add_error(msg)
                            break

                    # Save the state of all allocated servers
                    for s in resources['servers']:
                        state = {s['id']: {'state': s['state'],
                                           'type': 'resource',
                                           'cp_name': cp['name'],
                                           'resource_name': r_name,
                                           'member_id': s['member_id']}}
                        self._server_allocation_state_persistor.persist_info(state)

        # Remove the parent relationships in server_groups
        # now we're done processign because it causes a
        # circular reference
        for group_name, group in server_groups.iteritems():
            ServerGroup.clear_parent(group)

        # Resolve the networks for each server
        self.explain_block("Resolve Networks for Servers")
        for cp_name, cp in control_planes.iteritems():
            cp_prefix = cp.get('control-plane-prefix', cp['name'])
            hostname_prefix = "%s-%s" % (hostname_data['host-prefix'], cp_prefix)
            for cluster in cp['clusters']:
                for s in cluster['servers']:
                    self.resolve_server_networks(s, components, network_groups, network_addresses,
                                                 cluster, hostname_prefix)

            if 'resources' in cp:
                for r_name, resources in cp['resources'].iteritems():
                    for s in resources['servers']:
                        self.resolve_server_networks(s, components, network_groups, network_addresses,
                                                     resources, hostname_prefix)

        # Populate the service views
        service_view = {'by_region': {},
                        'by_service': {},
                        'by_rack': {}}

        for cp_name in sorted(control_planes):
            cp = control_planes[cp_name]
            cp_service_view = service_view['by_region'][cp_name] = {}

            cp['components'] = {}

            for cluster in cp['clusters']:
                for s in cluster['servers']:
                    for component_name in s['components']:
                        component = components.get(component_name, {})
                        component_parent = component.get('service', 'foundation')

                        # Add to list of components in this cp
                        if component_name not in cp['components']:
                            cp['components'][component_name] = {'hosts': []}
                        cp['components'][component_name]['hosts'].append(s['hostname'])

                        # Add to by region service view
                        if component_parent not in cp_service_view:
                            cp_service_view[component_parent] = {}
                        if component_name not in cp_service_view[component_parent]:
                            cp_service_view[component_parent][component_name] = []
                        cp_service_view[component_parent][component_name].append(s['hostname'])

                        # Add to by_service service view
                        if component_parent not in service_view['by_service']:
                            service_view['by_service'][component_parent] = {}
                        if cp_name not in service_view['by_service'][component_parent]:
                            service_view['by_service'][component_parent][cp_name] = {}
                        if component_name not in service_view['by_service'][component_parent][cp_name]:
                            service_view['by_service'][component_parent][cp_name][component_name] = []
                        service_view['by_service'][component_parent][cp_name][component_name].append(s['hostname'])

                        # Add to by_rack service view
                        if s['rack'] not in service_view['by_rack']:
                            service_view['by_rack'][s['rack']] = {}
                        if s['hostname'] not in service_view['by_rack'][s['rack']]:
                            s_view = service_view['by_rack'][s['rack']][s['hostname']] = {}
                        if component_parent not in s_view:
                            s_view[component_parent] = []
                        if component_name not in s_view[component_parent]:
                            s_view[component_parent].append(component_name)

            if 'resources' in cp:

                for r_name, resources in cp['resources'].iteritems():
                    for s in resources['servers']:
                        for component_name in s['components']:
                            component = components.get(component_name, {})
                            component_parent = component.get('service', 'foundation')

                            # Add to list of components in this cp
                            if component_name not in cp['components']:
                                cp['components'][component_name] = {'hosts': []}
                            cp['components'][component_name]['hosts'].append(s['hostname'])

                            # Add to by region service view
                            if component_parent not in cp_service_view:
                                cp_service_view[component_parent] = {}
                            if component_name not in cp_service_view[component_parent]:
                                cp_service_view[component_parent][component_name] = []
                            cp_service_view[component_parent][component_name].append(s['hostname'])

                            # Add to by_service service view
                            if component_parent not in service_view['by_service']:
                                service_view['by_service'][component_parent] = {}
                            if cp_name not in service_view['by_service'][component_parent]:
                                service_view['by_service'][component_parent][cp_name] = {}
                            if component_name not in service_view['by_service'][component_parent][cp_name]:
                                service_view['by_service'][component_parent][cp_name][component_name] = []
                            service_view['by_service'][component_parent][cp_name][component_name].append(s['hostname'])

                            # Add to by_rack service view
                            if s['rack'] not in service_view['by_rack']:
                                service_view['by_rack'][s['rack']] = {}
                            if s['hostname'] not in service_view['by_rack'][s['rack']]:
                                s_view = service_view['by_rack'][s['rack']][s['hostname']] = {}
                            if component_parent not in s_view:
                                s_view[component_parent] = []
                            if component_name not in s_view[component_parent]:
                                s_view[component_parent].append(component_name)

        #
        # Add network routes and VIPs
        #

        for cp_name in sorted(control_planes):
            cp = control_planes[cp_name]

            # build a list of all servers in the region
            region_servers = []
            for cluster in cp['clusters']:
                for s in cluster['servers']:
                    region_servers.append(s)

            for r_name, resources in cp.get('resources', {}).iteritems():
                for s in resources['servers']:
                    region_servers.append(s)

            # Find all of the networks, services and endpoints in this region
            region_components = set()
            region_networks = set()
            region_network_groups = set()
            region_endpoints = {}

            for cluster in cp['clusters']:
                for component_name in cluster['service-components']:
                    region_components.add(component_name)

            for s in region_servers:
                for iface_name, iface in s['interfaces'].iteritems():
                    for net_name, net in iface['networks'].iteritems():
                        region_networks.add(net_name)
                        region_network_groups.add(net['network-group'])
                        for component_name, ep in net['endpoints'].iteritems():
                            if component_name not in region_endpoints:
                                region_endpoints[component_name] = {'network-group': net['network-group'],
                                                                    'host-tls': ep['use-tls'],
                                                                    'hosts': [],
                                                                    'has-vip': False}
                            region_endpoints[component_name]['hosts'].append(
                                {'hostname': net['hostname'],
                                 'network': net['name'],
                                 'ip_address': net['addr'],
                                 'member_id': s['member_id']})

            self.explain_block("Resolve Network Routes")
            region_routes = {}
            # Add routes to each network for any other networks in the same group in this region
            for net_name in region_networks:
                net = networks[net_name]
                if net_name not in region_routes:
                    region_routes[net_name] = []
                for other_net_name in region_networks:
                    other_net = networks[other_net_name]
                    if (net != other_net and
                            net['network-group'] == other_net['network-group']):
                        self.explain("Add route from %s to %s (same group)" % (net_name, other_net_name))
                        route_data = {'cidr': other_net['cidr'],
                                      'net_name': other_net['name'],
                                      'implicit': True,
                                      'default': False}
                        region_routes[net_name].append(route_data)

                # Add other routes required by this group
                for route in network_groups[net['network-group']].get('routes', []):
                    if route in network_groups:
                        # If this is a route to another group, add in all of the netwokrs in that group
                        for other_net in network_groups[route].get('networks', []):
                            self.explain("Add route from %s to %s (another group)" %
                                         (net_name, other_net['name']))
                            route_data = {'cidr': other_net['cidr'],
                                          'net_name': other_net['name'],
                                          'implicit': False,
                                          'default': False}
                            region_routes[net_name].append(route_data)
                    elif route == 'default':
                        self.explain("Add route from %s to 0.0.0.0/0 (default)" %
                                     (net_name))
                        route_data = {'cidr': '0.0.0.0/0',
                                      'net_name': None,
                                      'implicit': False,
                                      'default': True}
                        region_routes[net_name].append(route_data)
                    else:
                        msg = ("Invalid route '%s' in network group %s - "
                               "must be a network group name or 'default'." %
                               (route, net['network-group']))
                        self.add_error(msg)

            # Add the routes for each server
            self.explain_block("Resolve Network Routes for each server")
            for s in region_servers:
                self.explain_block("server: %s" % s['name'], level=1)
                # Find the list of all networks we have an implcit route to
                implicit_routes = set()
                for iface_name, iface in s['interfaces'].iteritems():
                    for net_name, net in iface['networks'].iteritems():
                        implicit_routes.add(net_name)
                        for route_data in region_routes.get(net['name'], []):
                            if route_data['implicit']:
                                implicit_routes.add(route_data['net_name'])

                for iface_name, iface in s['interfaces'].iteritems():
                    for net_name, net in iface['networks'].iteritems():
                        net['routes'] = []
                        for route_data in region_routes.get(net['name'], []):
                            if not route_data['implicit'] and route_data['net_name'] in implicit_routes:
                                self.explain("Skip %s -> %s (%s) as covered by an implicit route" %
                                             (net_name, route_data['cidr'], route_data['net_name']))
                            else:
                                self.explain("Add %s -> %s (%s)" %
                                             (net_name, route_data['cidr'], route_data['net_name']))
                                net['routes'].append(route_data)

            # Find networks that have Load Balancers
            vip_networks = {}
            vips_by_role = {}
            self.explain_block("Define load balancers")
            for lb in load_balancers:
                self.explain_block("Load balancer: %s" % lb['name'], level=1)
                address = ''
                vip_net_group = lb.get('network-group', 'External')

                vip_provider = lb.get('provider', 'external')
                if vip_provider == 'external':
                    vip_net = "External"
                    for ext_ep in lb.get('vip-address', []):
                        if ext_ep['region'] == cp.get('region-name', '') or ext_ep['region'] == "*":
                            address = ext_ep.get('ip-address', '???')
                            cert_file = ext_ep.get('cert-file', '')
                    if not address:
                        continue
                else:
                    # Find the servers running the vip_provider
                    vip_nets = {}
                    for vip_server in cp['components'][vip_provider]['hosts']:
                        vip_net = self._get_network_in_netgroup_for_server(vip_net_group, vip_server, region_servers)
                        if not vip_net:
                            msg = ("Server '%s' provides the '%s' service for load balancer '%s' "
                                   "but it is not connected to a network in network group '%s'" %
                                   (vip_server, vip_provider, lb['name'], vip_net_group))
                            self.add_error(msg)
                            continue
                        vip_nets[vip_net] = vip_server

                    if len(vip_nets) > 1:
                        msg = ("Load Balancer providers on different networks\n"
                               "The following servers provide the '%s' service for load balancer '%s' "
                               "in network group '%s' but are on different networks:\n" %
                               (vip_provider, lb['name'], vip_net_group))
                        for vip_net, vip_server in vip_nets.iteritems():
                            msg += "    %s:  network %s\n" % (vip_server, vip_net)
                        self.add_error(msg)
                        continue
                    else:
                        vip_net = vip_nets.keys()[0]

                    cert_file = lb.get('cert-file', '')

                    # If services on this LB share a vip allocate it now

                    if lb.get('shared-address', True):

                        vip_name = "%s-%s-vip-%s-%s" % (
                            hostname_data['host-prefix'],
                            cp.get('control-plane-prefix', cp['name']),
                            lb.get('name', 'lb'),
                            network_groups[vip_net_group].get(
                                'hostname-suffix',
                                network_groups[vip_net_group]['name']))

                        address = self.allocate_address(
                            network_addresses[vip_net],
                            "vip %s" % (lb['name']),
                            vip_name, vip_net)

                # See if cert_file is really a list of per service cert_files
                if cert_file:
                    if isinstance(cert_file, basestring):
                        cert_list = {'default': cert_file}
                    else:
                        cert_list = cert_file
                else:
                    cert_list = None

                #
                # Loop through all services in thie region, and find which need
                # to have a vip on this LB. A service might be excplictly on a
                # lb, or included as "default"
                #

                #
                # When not sharing VIPs between services we need to keep track of them
                #
                component_vips = {}

                for component_name, component_endpoint in region_endpoints.iteritems():

                    lb_components = lb.get('components', []) + lb.get('tls-components', [])

                    if (component_name in lb_components or "default" in lb_components):
                        for component_ep in components.get(component_name, {}).get('endpoints', []):
                            if component_ep.get('has-vip'):

                                # Check Service allows this VIP role
                                vip_roles = [r for r in lb.get('roles', [])
                                             if r in component_ep.get('roles', [])]
                                if not vip_roles:
                                    continue

                                # So now we know that ths component should have a VIP on this LB
                                # for one or more of its roles.
                                if 'internal' in vip_roles:
                                    region_endpoints[component_name]['has-vip'] = True

                                # Create an entry in vip_networks
                                # for this network if it doesn't already exist

                                if vip_net not in vip_networks:
                                    vip_networks[vip_net] = []

                                # Build an Alias for the VIP for this component
                                vip_alias = {}
                                for role in vip_roles:
                                    if role == 'internal':
                                        alias = "%s-%s-vip-%s-%s" % (
                                            hostname_data['host-prefix'],
                                            cp.get('control-plane-prefix', cp['name']),
                                            components[component_name]['mnemonic'],
                                            network_groups[vip_net_group].get(
                                                'hostname-suffix',
                                                network_groups[vip_net_group]['name']))
                                    else:
                                        alias = "%s-%s-vip-%s-%s-%s" % (
                                            hostname_data['host-prefix'],
                                            cp.get('control-plane-prefix', cp['name']),
                                            role,
                                            components[component_name]['mnemonic'],
                                            network_groups[vip_net_group].get(
                                                'hostname-suffix',
                                                network_groups[vip_net_group]['name']))

                                    vip_alias[role] = alias

                                # If we have a shared address create an alias
                                if lb.get('shared-address', True):
                                    for alias_role, alias in vip_alias.iteritems():
                                        self.add_hostname_alias(networks[vip_net], address, alias)

                                else:
                                    # See if we already have an address for this VIP
                                    if component_name in component_vips:
                                        address = component_vips[component_name]
                                    else:
                                        # Allocate an address for the vip for this component
                                        if 'internal' in vip_roles:
                                            vip_name = vip_alias['internal']
                                        elif 'public' in vip_roles:
                                            vip_name = vip_alias['public']
                                        else:
                                            vip_name = vip_alias[0]

                                        address = self.allocate_address(
                                            network_addresses[vip_net],
                                            "vip for %s" % component_name,
                                            vip_name, vip_net)
                                        component_vips[component_name] = address

                                    for alias_role, alias in vip_alias.iteritems():
                                        if vip_name != alias:
                                            self.add_hostname_alias(networks[vip_net], address, alias)

                                # Always use the service name / alias for clarity in haproxy config
                                if 'internal' in vip_roles:
                                    vip_hostname = vip_alias['internal']
                                elif 'admin' in vip_roles:
                                    vip_hostname = vip_alias['admin']
                                elif 'public' in vip_roles:
                                    vip_hostname = vip_alias['public']
                                else:
                                    vip_hostname = vip_alias.keys()[0]

                                # Is this a component or an tls_component
                                if component_name in lb.get('components', []):
                                    vip_tls = False
                                elif (component_name in lb.get('tls-components', [])
                                        or "default" in lb.get('tls-components', [])):
                                    vip_tls = True
                                else:
                                    vip_tls = False

                                # Create an entry for the vip for this component
                                vip_data = {
                                    'component-name': component_name,
                                    'provider': lb.get('provider', "External"),
                                    'vip-port': component_ep.get('vip-port',
                                                                 component_ep['port']),
                                    'host-port': component_ep['port'],
                                    'target': component_endpoint['network-group'],
                                    'hosts': component_endpoint['hosts'],
                                    'host-tls': component_endpoint['host-tls'],
                                    'roles': vip_roles,
                                    'advertise': False,
                                    'address': address,
                                    'network': vip_net,
                                    'network-group': vip_net_group,
                                    'aliases': {},
                                    'hostname': vip_hostname,
                                    'vip-tls': vip_tls
                                }

                                if vip_tls and 'vip-tls-port' in component_ep:
                                    vip_data['vip-port'] = component_ep['vip-tls-port']

                                vip_data['aliases'] = vip_alias

                                if lb.get('external-name'):
                                    vip_data['external-name'] = lb['external-name']

                                if cert_list:
                                    cert = cert_list.get(component_name)
                                    if not cert:
                                        cert = cert_list.get('default')

                                    if cert:
                                        vip_data['cert-file'] = cert
                                    else:
                                        msg = ("Network group %s load balancer %s: "
                                               "cert-file supplied as a dict but no "
                                               "entry for 'default' or %s." %
                                               (vip_net_group, lb['name'], component_name))
                                        self.add_error(msg)

                                if 'vip-options' in component_ep:
                                    vip_data['vip-options'] = component_ep['vip-options']

                                if 'vip-check' in component_ep:
                                    vip_data['vip-check'] = component_ep['vip-check']

                                vip_data['vip-backup-mode'] = component_ep.get('vip-backup-mode',
                                                                               False)

                                # Record if the VIP is on this LB as part of the default set
                                if "default" in lb.get('components', []) + lb.get('tls-components', []):
                                    self.explain("Add %s for roles %s due to 'default'" % (component_name, vip_roles))
                                    vip_data['default'] = True
                                else:
                                    self.explain("Add %s for roles %s" % (component_name, vip_roles))
                                    vip_data['default'] = False

                                    # Keep track of the components added by name so we can remove
                                    # any entries for those components added to the list via a
                                    # "default" match for the same role.
                                    for role in vip_roles:
                                        if role not in vips_by_role:
                                            vips_by_role[role] = []
                                        vips_by_role[role].append(component_name)

                                # See if this endpoint should be advertised
                                if 'advertises-to-services' in \
                                        components[component_name]:
                                    vip_data['advertise'] = True

                                vip_networks[vip_net].append(vip_data)

            # Can't do any more if we have errors when building the load balancers
            if self._errors:
                return

            # Save the results in the cp
            cp['vip_networks'] = vip_networks

            # Now we have a full list of LBs on all networks build a list of
            # load-balancers by provider (e.g. ip-cluster) form this control plane.
            # Note that a CP load balancer will serve the VIPs for multiple load-balancers
            # in the input model (for example the public and internal LBs will be separate
            # in network groups but are provided by the same ip-cluster service
            #
            self.explain_block("Map load balancers to providers")
            cp['load-balancers'] = {}
            component_vips = {}
            for vip_net_name, vip_net in vip_networks.iteritems():
                self.explain_block("Network %s" % vip_net_name, level=1)
                for vip_data in vip_net:
                    vip_component_name = vip_data['component-name']

                    # If this VIP was added as a result of a "default" set on a
                    # Load balancer check to see if it has any explcit roles on another
                    # LB.  If it does remove those roles from this VIP.
                    if vip_data['default']:
                        default_roles = []
                        for role in vip_data['roles']:
                            if vip_component_name not in vips_by_role.get(role, []):
                                default_roles.append(role)
                        vip_data['roles'] = default_roles

                    # We might have removed all of the roles in the above
                    if not vip_data['roles']:
                        continue

                    if vip_data['provider'] not in cp['load-balancers']:
                        cp['load-balancers'][vip_data['provider']] = {}

                    if vip_component_name not in cp['load-balancers'][vip_data['provider']]:

                        cp['load-balancers'][vip_data['provider']][vip_component_name] = {
                            'hosts': vip_data['hosts'],
                            'host-tls': vip_data['host-tls'],
                            'networks': []
                        }

                    # NOTE: If the host is terminating TLS then stunnel will listen on
                    # the vip-port not the host-port.  Normally these are the same but
                    # they can be different if an service can't allow anything else to
                    # bind to the same port - for example vertica always binds to
                    # its port on 0.0.0.0 so haproxy and stunnel can't use the same port
                    if vip_data['host-tls']:
                        host_port = vip_data['vip-port']
                    else:
                        host_port = vip_data['host-port']

                    lb_networks = cp['load-balancers'][vip_data['provider']][vip_component_name]['networks']
                    self.explain("%s: %s %s roles: %s vip-port: %s host-port: %s" %
                                 (vip_data['address'], vip_data['provider'], vip_component_name,
                                  vip_data['roles'], vip_data['vip-port'], host_port))
                    lb_data = {
                        'component-name': vip_data['component-name'],
                        'hostname': vip_data['hostname'],
                        'ip-address': vip_data['address'],
                        'network': vip_data['network'],
                        'network-group': vip_data['network-group'],
                        'vip-port': vip_data['vip-port'],
                        'host-port': host_port,
                        'roles': vip_data['roles'],
                        'vip-tls': vip_data['vip-tls']
                    }

                    # Copy accross any optional items.  Use deepcopy() beacuse the item may
                    # be one more than one VIP, and we dont't want reference tags in the
                    # output yaml
                    for item in ['cert-file', 'vip-options', 'vip-check', 'vip-backup-mode']:
                        if item in vip_data:
                            lb_data[item] = deepcopy(vip_data[item])

                    lb_networks.append(lb_data)

                    # Keep a map from component/role to the vip to make it
                    # easy to find them
                    if vip_component_name not in component_vips:
                        component_vips[vip_component_name] = {}

                    for role in vip_data['roles']:
                        component_vips[vip_component_name][role] = vip_data

            #
            # Build a list of all of the endpoints that are to be advertised
            #
            cp['advertises'] = {}
            for vip_net_name, vip_net in vip_networks.iteritems():
                for vip_data in vip_net:
                    vip_component_name = vip_data['component-name']

                    # Because of we add all services for a "default" rule and
                    # then remove any explict roles on another LB we might end
                    # up with no roles
                    if not vip_data['roles']:
                        continue

                    if vip_data.get('advertise'):
                        if vip_component_name not in cp['advertises']:
                            cp['advertises'][vip_component_name] = {}

                        for r in vip_data['roles']:
                            if vip_data['vip-tls']:
                                protocol = 'https'
                            else:
                                protocol = 'http'

                            # Use IP address for URLs in keystone
                            url = "%s://%s:%s" % (
                                protocol,
                                vip_data.get('external-name', vip_data['address']),
                                vip_data['vip-port'])

                            data = {
                                'hostname': vip_data['hostname'],
                                'ip_address': vip_data['address'],
                                'port': vip_data['vip-port'],
                                'protocol': protocol,
                                'use_tls': vip_data['vip-tls'],
                                'url': url
                            }
                            cp['advertises'][vip_component_name][r] = data

            #
            # Build a list of endpoints for the control plane
            #
            #  access - what do clients call
            #  bind  - what does the sevice listen on
            #  tls_term - what does the tls terminator listen on
            #  tls_init - what does an tls initiator connect to
            endpoints = {}
            for component_name, endpoint in region_endpoints.iteritems():
                for component_ep in components.get(component_name, {}).get('endpoints', []):
                    if component_name not in endpoints:
                        endpoints[component_name] = {}

                    for role in component_ep.get('roles', []):
                        if role not in endpoints[component_name]:
                            endpoints[component_name][role] = []
                        endpoint_data = {}

                        if component_ep.get('has-vip', False):
                            # Find the vip for this role
                            if role not in component_vips[component_name]:
                                msg = ("Component %s needs a VIP for role %s "
                                       "but there is no load-balancer providing "
                                       "that role." % (component_name, role))
                                self.add_error(msg)
                                continue

                            vip_data = component_vips[component_name][role]

                            # Components that need a TLS initiatior have to be accessed
                            # via localhost and have the TLS initiator configured
                            if vip_data['vip-tls'] and component_ep.get('tls-initiator', False):
                                endpoint_data['access'] = {
                                    'network': vip_data['network'],
                                    'address': '127.0.0.1',
                                    'hostname': 'localhost',
                                    'port': vip_data['vip-port'],
                                    'use-tls': False}
                                endpoint_data['tls-init'] = {
                                    'address': vip_data['address'],
                                    'hostname': vip_data['aliases'][role],
                                    'port': vip_data['vip-port'],
                                    'use-tls': True}
                            else:
                                endpoint_data['access'] = {
                                    'network': vip_data['network'],
                                    'address': vip_data['address'],
                                    'hostname': vip_data['aliases'][role],
                                    'port': vip_data['vip-port'],
                                    'use-tls': vip_data['vip-tls']}

                            # If the service endpoint is TSL enabled then the service needs to
                            # bind to localhost and a tls terminator configured
                            if endpoint['host-tls']:
                                endpoint_data['bind'] = {
                                    'address': '127.0.0.1',
                                    'port': vip_data['host-port']}

                                # NOTE: Tell stunnel to use the vip-port
                                # because where this is different from the
                                # host-port it normally means that nothing
                                # apart from the service can use that port.
                                endpoint_data['tls-term'] = {
                                    'network_group': vip_data['target'],
                                    'port': vip_data['vip-port']}
                            else:
                                endpoint_data['bind'] = {
                                    'network_group': vip_data['target'],
                                    'port': vip_data['host-port']}

                            # Check if the component wants to also have its members listed
                            if component_ep.get('list-members', False):
                                endpoint_data['access']['members'] = endpoint['hosts']

                        else:
                            # No VIP - so add list of members instead
                            endpoint_data['access'] = {
                                'members': endpoint['hosts'],
                                'port': component_ep['port'],
                                'use-tls': endpoint['host-tls']}

                            if endpoint['host-tls']:
                                endpoint_data['bind'] = {
                                    'address': '127.0.0.1',
                                    'port': component_ep['port']}
                                endpoint_data['tls-term'] = {
                                    'network_group': endpoint['network-group'],
                                    'port': component_ep['port']}
                            else:
                                endpoint_data['bind'] = {
                                    'network_group': endpoint['network-group'],
                                    'port': component_ep['port']}

                        endpoints[component_name][role].append(endpoint_data)

            cp['endpoints'] = endpoints

            # Add internal endpoints to services
            for component_name, component in cp['components'].iteritems():
                vip_data = component_vips.get(component_name, {}).get('internal', {})
                if vip_data:
                    component['endpoint'] = {'ip_address': vip_data['address'],
                                             'port': vip_data['vip-port']}
                    component['targets'] = vip_data['hosts']
                elif component_name in cp['endpoints']:
                    endpoint_data = cp['endpoints'][component_name]
                    if 'internal' in endpoint_data:
                        # TODO-PHIL:   Not sure that takign the first entry when there are muliple
                        # internal endpoints is teh rigth thing to do.  Only Monastca-threshold hits
                        # this I think
                        endpoint_data = endpoint_data['internal'][0]['access']
                        component['endpoint'] = endpoint_data['port']
                        component['targets'] = endpoint_data['members']

            # Build a list of members by service
            cp['members'] = {}
            for component_name, r_endpoint in region_endpoints.iteritems():
                for endpoint in components[component_name].get('endpoints', []):
                    if component_name not in cp['members']:
                        cp['members'][component_name] = {'hosts': r_endpoint['hosts'],
                                                         'ports': {}}
                        member_data = cp['members'][component_name]
                    for role in endpoint.get('roles', []):
                        if role not in member_data['ports']:
                            member_data['ports'][role] = []
                        member_data['ports'][role].append(endpoint['port'])

        # Build a list of allocated addresses
        allocated_addresses = {}
        persisted_unused = {}
        for group_name, group in network_groups.iteritems():
            allocated_addresses[group_name] = {}
            for network in group['networks']:
                allocated_addresses[group_name][network['name']] = {}
                for addr in network_addresses[network['name']]:
                    if addr['allocated']:
                        allocated_addresses[group_name][network['name']][addr['addr']] = {'host': addr['host'],
                                                                                          'used-by': addr['used-by']}
                    elif addr['persisted']:
                        if network['name'] not in persisted_unused:
                            persisted_unused[network['name']] = []
                        persisted_unused[network['name']].append(addr)

        # Handle any persisted addresses that we are not using any more
        addr_msg = ""
        for net_name, addresses in persisted_unused.iteritems():
            for addr_data in addresses:
                if free_unused_addresses:
                    self._address_state_persistor.delete_info([addr_data['addr']])
                else:
                    addr_msg += ("\n         %s (%s - %s %s)" %
                                 (addr_data['addr'], net_name, addr_data['used-by'], addr_data['host']))

        if addr_msg:
            msg = ("Unused persisted address allocations\n"
                   "The following address allocations are persisted but not used: "
                   "%s\n"
                   "    To free these addresses rerun the config processor with "
                   "'--free_unused_addresses'" % addr_msg)
            self.add_warning(msg)

        ntp_servers = cloud_data.get('ntp-servers', [])
        dns_settings = cloud_data.get('dns-settings', {})
        smtp_settings = cloud_data.get('smtp-settings', {})
        firewall_settings = cloud_data.get('firewall-settings', {})

        cloud_internal = CloudModel.internal(self._models['CloudModel'])
        CloudModel.put(cloud_internal, 'control-planes', control_planes)
        CloudModel.put(cloud_internal, 'service_view', service_view)
        CloudModel.put(cloud_internal, 'address_allocations', allocated_addresses)
        CloudModel.put(cloud_internal, 'host_aliases', self.host_aliases)
        CloudModel.put(cloud_internal, 'networks', networks)
        CloudModel.put(cloud_internal, 'servers', servers)
        CloudModel.put(cloud_internal, 'server-groups', server_groups)
        CloudModel.put(cloud_internal, 'services', services)
        CloudModel.put(cloud_internal, 'components', components)
        CloudModel.put(cloud_internal, 'components_by_mnemonic', components_by_mnemonic)
        CloudModel.put(cloud_internal, 'ntp_servers', ntp_servers)
        CloudModel.put(cloud_internal, 'dns_settings', dns_settings)
        CloudModel.put(cloud_internal, 'smtp_settings', smtp_settings)
        CloudModel.put(cloud_internal, 'firewall_settings', firewall_settings)
        CloudModel.put(cloud_internal, 'pass_through', pass_through)

        self.write_explanation()

    #
    # Update the list of zone-types in a control plane based
    # on a list of components.  Component define which zone types any
    # server they are running on should be included in.  For example
    # nova-compute in its service definition will have:
    #
    #    zone-type: nova_availability_zones
    #
    # Building these per service makes it easier for a playbook to
    # see when it has to create zones in a particular control plane and
    # seperate zone creation from adding individual servers to a zone
    #
    @staticmethod
    def _update_cp_zones(cp, zones, component_list, components):
        for comp_name in component_list:
            zone_type = components[comp_name].get('zone-type')
            if zone_type:
                if zone_type not in cp['zone-types']:
                    cp['zone-types'][zone_type] = set()
                for zone in zones:
                    cp['zone-types'][zone_type].add(zone)

    #
    # Update a component list with any required service dependencies
    #
    def _add_required_services_to_cp(self, cp, components):

        def _add_required(component_list, context):
            for comp_name in component_list:
                for requires in components[comp_name].get('requires', []):
                    required_comp = requires.get('name')
                    if (requires.get('scope') == 'host'
                            and required_comp not in component_list):
                        component_list.append(required_comp)
                        self.explain("%s: Added %s required by %s" %
                                     (context, required_comp, comp_name))

        self.explain_block("Add required services to control plane %s" % cp['name'])

        for cluster in cp['clusters']:
            _add_required(cluster['service-components'], cp['name'])

        for r in cp.get('resources', []):
            _add_required(r['service-components'], r['name'])

    #
    # Add a server to a cluster
    #
    @staticmethod
    def _add_server_to_cluster(s, member_id, zone_name, cp, cluster, hostname_data):
        s['state'] = ServerState.ALLOCATED
        s['member_id'] = member_id
        s['failure-zone'] = zone_name
        s['components'] = cluster['service-components']
        s['services'] = cluster['services']
        s['region'] = cp['region-name']

        name = "%s-%s-%s" % (hostname_data['host-prefix'],
                             cp.get('control-plane-prefix', cp['name']),
                             cluster.get('cluster-prefix', cluster['name']))
        s['name'] = name + "%s%d" % (hostname_data.get('member-prefix', ''),
                                     s['member_id'])
        cluster['servers'].append(s)

    #
    # Add a server to a resource group
    #
    @staticmethod
    def _add_server_to_resources(s, member_id, zone_name, cp, resources, hostname_data):
        s['state'] = ServerState.ALLOCATED
        s['member_id'] = member_id
        s['failure-zone'] = zone_name
        s['components'] = resources['service-components']
        s['services'] = resources['services']
        s['region'] = cp['region-name']

        name = "%s-%s-%s%04d" % (hostname_data['host-prefix'],
                                 cp.get('control-plane-prefix', cp['name']),
                                 resources.get('resource-prefix', resources['name']),
                                 s['member_id'])
        s['name'] = name
        resources['servers'].append(s)

    #
    # Find network in network_group for a specific server in a list of servers
    #
    @staticmethod
    def _get_network_in_netgroup_for_server(net_group, server_name, servers):
        network = None
        for s in servers:
            if s.get('hostname') != server_name:
                continue
            for iface_name, iface in s.get('interfaces', {}).iteritems():
                for net_name, net_data in iface.get('networks', {}).iteritems():
                    if net_data['network-group'] == net_group:
                        network = net_name
                        break
        return network

    #
    # Generate addresses and load persisted address allocations
    #
    def generate_addresses(self, addresses, server_addresses):
        for f in addresses:
            addr = f['addr']

            pi = self._address_state_persistor.recall_info([addr])
            if pi:
                f['free'] = bool(pi['free'])
                f['used-by'] = pi['used-by']
                f['host'] = pi['host']
                f['server-id'] = pi.get('server-id')
                f['persisted'] = True
                f['allocated'] = False
            elif addr in server_addresses:
                f['free'] = False
                f['used-by'] = ""
                f['host'] = ""
                f['server-id'] = server_addresses[addr]
                f['persisted'] = False
                f['allocated'] = False
            else:
                f['free'] = True
                f['used-by'] = ""
                f['host'] = ""
                f['server-id'] = ""
                f['persisted'] = False
                f['allocated'] = False

    #
    # Allocate an address from a network or return a previously allocated
    # address
    #
    def allocate_address(self, addresses, used_by, host="", net_name="",
                         addr=None, server_id=None):

        """ Allocate an address from a list of addresses
        :param addresses:  A list of address structures to allocate from
        :param used_by: A string that records what the address is being used by
        :param host: The host name to be assocated with the address
        :param net_name:  The name of the network we're allocating from
        :param addr: A specific address to be allocated. Used when we're taking
                     an existing address from a server
        :param server_id: The ID of the server the address is allocated to
        """

        result = None
        for f in addresses:

            if addr:
                if f['addr'] != addr:
                    continue
                elif f['free'] or f['host'] == host or f['server-id'] == server_id:
                    result = f
                    self.explain("Using address %s for %s %s on network %s" %
                                 (addr, used_by, host, net_name))
                    break
                else:
                    msg = ("Could not allocate address %s from network %s "
                           "for %s %s, already used by %s %s" %
                           (addr, net_name,
                            used_by, host, f['used-by'], f['host']))
                    self.add_error(msg)

            elif f['used-by'] == used_by and f['host'] == host:
                result = f
                self.explain("Using persisted address %s for %s %s on network %s" %
                             (f['addr'], used_by, host, net_name))
                break

        # Didn't find one, so look for a free address
        if not result and not addr:
            for f in addresses:
                if f['free']:
                    self.explain("Allocated address %s for %s %s on network %s" %
                                 (f['addr'], used_by, host, net_name))
                    result = f
                    break

        if result:
            # Always (re)persist the allocation, so that if we've changed the
            # set of data it gets updated
            addr = f['addr']
            f['free'] = False
            f['used-by'] = used_by
            f['host'] = host
            f['server-id'] = server_id
            f['allocated'] = True

            pi = {addr: f}
            self._address_state_persistor.persist_info(pi)

            return result['addr']
        else:
            msg = ("Could not allocate address from network %s "
                   "for %s %s" % (net_name, used_by, host))
            self.add_error(msg)

            return None

    # ---------------------------------------
    # Record host name aliases
    # ---------------------------------------
    host_aliases = {}

    def add_hostname_alias(self, net, address, name):

        if net['network-group'] not in self.host_aliases:
            self.host_aliases[net['network-group']] = {}

        if net['name'] not in self.host_aliases[net['network-group']]:
            self.host_aliases[net['network-group']][net['name']] = {}

        if address not in self.host_aliases[net['network-group']][net['name']]:
            self.host_aliases[net['network-group']][net['name']][address] = set()

        self.host_aliases[net['network-group']][net['name']][address].add(name)

    # ----------------------------------------------
    # Check if we can take over an existing address
    # ----------------------------------------------
    def consume_address(self, addr, net):

        ip_net = IPNetwork(unicode(net['cidr']))
        net_start = ip_net[1]
        net_end = ip_net[-2]

        # Note:  Start and End address (if present) have
        # already been validated to be in the cidr
        if 'start-address' in net:
            net_start = IPAddress(net['start-address'])

        if 'end-address' in net:
            net_end = IPAddress(net['end-address'])

        if net_start <= IPAddress(addr) <= net_end:
            return addr
        else:
            return None

    # ---------------------------------------
    # Resolve network config for a server.
    # ---------------------------------------
    def resolve_server_networks(self, s, components, network_groups, network_addresses,
                                cluster, hostname_prefix):

        # Find which networks we need for this server
        required_nets = set()
        related_nets = {}
        components_included = set()
        tags_found = set()

        self.explain_block("server: %s" % s['name'], level=1)

        for group_name, net_group in network_groups.iteritems():

            # Build a list of all components on ths network
            component_endpoints = (
                net_group.get('component-endpoints', []) +
                net_group.get('tls-component-endpoints', [])
            )
            for lb in net_group.get('load-balancers', []):
                component_endpoints.append(lb['provider'])

            for component_name in s['components']:

                if component_name not in component_endpoints:
                    continue

                component = components.get(component_name, {})

                if (component_name in component_endpoints):
                    self.explain("add %s for component %s" % (group_name, component_name))
                    required_nets.add(group_name)
                    components_included.add(component_name)
                    self._add_auto_tags(component, net_group)

        # Add in entries for default endpoints, network tags, or default route
        for group_name, net_group in network_groups.iteritems():

            component_endpoints = (
                net_group.get('component-endpoints', []) +
                net_group.get('tls-component-endpoints', [])
            )

            for component_name in s['components']:
                component = components.get(component_name, {})

                if ('default' in component_endpoints
                        and component_name not in components_included):
                    self.explain("add %s for %s (default)" % (group_name, component_name))
                    required_nets.add(group_name)
                    self._add_auto_tags(component, net_group)

                # Add any networks that are required due to a service tag
                network_group_tags = net_group.get('tags', [])
                for tag in network_group_tags:
                    if tag.get('component', '') == component['name']:
                        # Add to the list of required networks
                        self.explain("add %s for tag %s (%s)" %
                                     (group_name, tag['name'], component['name']))
                        required_nets.add(group_name)

                        # Add to the list of related networks
                        if group_name not in related_nets:
                            related_nets[group_name] = []

                        related_nets[group_name].append(tag)

                        # Recored that we found the tag
                        tags_found.add(tag['name'])

        # Build a new list of networks limited to the ones needed on this server
        components_attached = set()
        server_network_groups = set()
        net_group_default_routes = []
        server_network_found = False

        for iface in s['interfaces']:
            iface_networks = {}
            iface_network_groups = []
            for net_name, net in iface['networks'].iteritems():
                if net['network-group'] in required_nets or net['forced']:
                    iface_networks[net_name] = net
                    server_network_groups.add(net['network-group'])
                    iface_network_groups.append(net['network-group'])

            iface['networks'] = iface_networks
            iface['network-groups'] = iface_network_groups

            for net_name, net in iface['networks'].iteritems():
                if 'cidr' in net:
                    server_addr = self.consume_address(s['addr'], net)
                    if server_addr:
                        server_network_found = True
                    net['addr'] = self.allocate_address(
                        network_addresses[net['name']],
                        used_by='server', host=s['name'],
                        net_name=net_name, addr=server_addr,
                        server_id=s['id'])
                    net_group = network_groups[net['network-group']]
                    net_suffix = net_group.get('hostname-suffix', net['network-group'])
                    net['hostname'] = "%s-%s" % (s['name'], net_suffix)
                    self.add_hostname_alias(net, net['addr'], net['hostname'])

                    # Is this the network that gives us the hostname ?
                    if net_group.get('hostname', False):
                        s['hostname'] = net['hostname']

                    # Will this network give us a default route
                    if 'default' in net_group.get('routes', []):
                        net_group_default_routes.append(net_group['name'])

                net['endpoints'] = {}
                net_group = network_groups[net['network-group']]
                net_group_endpoints = net_group.get('component-endpoints', [])
                net_group_tls_endpoints = net_group.get('tls-component-endpoints', [])

                # Add explicit endpoint attachments
                for component_name in s['components']:
                    component = components.get(component_name, {})
                    if (component_name in net_group_endpoints):
                        components_attached.add(component_name)
                        net['endpoints'][component_name] = {'use-tls': False}
                    if (component_name in net_group_tls_endpoints):
                        components_attached.add(component_name)
                        net['endpoints'][component_name] = {'use-tls': True}
                # Mark any networks added as a tag
                net['service-tags'] = related_nets.get(net['network-group'], {})

        # Check we found a network to use as the hostname
        if not server_network_found:
            msg = ("Server %s (%s) using interface model %s does not have a "
                   "connection to a network which contains its address." %
                   (s['name'], s['addr'], s['if-model']))
            self.add_error(msg)

        # Check we have only one one default route
        # Check we found a network to use as the hostname
        if s.get('hostname') is None:
            msg = ("Server %s (%s) using interface model %s does not have a "
                   "connection to a network group with \"hostname: true\"" %
                   (s['name'], s['addr'], s['if-model']))
            self.add_error(msg)
            # to prevent key errors in the rest of the generator
            s['hostname'] = s['name']

        # Check we have only one one default route
        if len(net_group_default_routes) > 1:
            msg = ("Server %s (%s) using interface model %s has "
                   "more than one network group with a default route: %s"
                   % (s['name'], s['addr'], s['if-model'], net_group_default_routes))
            self.add_error(msg)

        # Check we found all the required and related networks
        for net_group in required_nets:
            if net_group not in server_network_groups:
                # Don't error on networks that are in required due to a tag
                if net_group not in related_nets:
                    msg = ("Server %s (%s) using interface model %s does not have a "
                           "connection to a required network group: %s" %
                           (s['name'], s['addr'], s['if-model'], net_group))
                    self.add_error(msg)

        for net_group_name, tag_list in related_nets.iteritems():
            for tag_data in tag_list:
                if net_group_name not in server_network_groups:
                    msg = ("Server %s (%s) using interface model %s: %s is not "
                           "directly connected to a network group with the tag: %s " %
                           (s['name'], s['addr'], s['if-model'],
                            tag_data['component'], tag_data['name']))

                    if 'required' in tag_data['definition']:
                        self.add_error(msg)
                    else:
                        self.add_warning(msg)

        # Check we found all the tags:
        for component_name in s['components']:
            tags = components[component_name].get('network-tags', [])
            for tag in tags:
                if (tag.get('expected') and tag['name'] not in tags_found):
                    msg = ("Network tag \"%s\" was expected by %s: %s" %
                           (tag['name'], component_name, tag['expected']))
                    self.add_warning(msg)
                elif (tag.get('required') and tag['name'] not in tags_found):
                    msg = ("Network tag \"%s\" is required by %s: %s" %
                           (tag['name'], component_name, tag['required']))
                    self.add_error(msg)

        # Add default endpoint attachments
        for iface in s['interfaces']:

            for net_name, net in iface['networks'].iteritems():
                net_group = network_groups[net['network-group']]
                net_group_endpoints = net_group.get('component-endpoints', [])
                net_group_tls_endpoints = net_group.get('tls-component-endpoints', [])

                for component_name in s['components']:
                    component = components.get(component_name, {})
                    if ('default' in net_group_endpoints
                            and component_name not in components_attached):
                        net['endpoints'][component_name] = {'use-tls': False}
                    elif ('default' in net_group_tls_endpoints
                            and component_name not in components_attached):
                        net['endpoints'][component_name] = {'use-tls': True}

        # Add service ips if required
        for iface in s['interfaces']:
            for net_name, net in iface['networks'].iteritems():
                for component_name in s['components']:
                    component = components.get(component_name, {})
                    if (component.get('needs-ip', 'False') is True
                            or component.get('needs-cluster-ip', 'False') is True):
                        if 'service-ips' not in cluster:
                            cluster['service-ips'] = {}
                        if component_name not in cluster['service-ips']:
                            cluster['service-ips'][component_name] = {}
                        if net_name not in cluster['service-ips'][component_name]:
                            cluster['service-ips'][component_name][net_name] = \
                                {'hosts': []}
                        service_ip_data = cluster['service-ips'][component_name][net_name]

                        if (component.get('needs-ip', 'False') is True
                                and component_name in net['endpoints']
                                and 'cidr' in net):
                            addr = self.allocate_address(
                                network_addresses[net['name']],
                                used_by=component_name, host=s['name'], net_name=net_name)
                            net_group = network_groups[net['network-group']]
                            net_suffix = net_group.get('hostname-suffix', net['network-group'])
                            alias = "%s-%s-%s" % (s['name'], component['mnemonic'],
                                                  net_suffix)
                            self.add_hostname_alias(net, addr, alias)

                            if 'service-ips' in s:
                                s['service-ips'][component_name] = addr
                            else:
                                s['service-ips'] = {}
                                s['service-ips'][component_name] = addr

                            service_ip_data['hosts'].append(
                                {'hostname': alias,
                                 'ip_address': addr})

                        if (component.get('needs-cluster-ip', 'False') is True
                                and component_name in net['endpoints']
                                and 'cidr' in net):
                            if 'cluster-ip' not in service_ip_data:
                                addr = self.allocate_address(
                                    network_addresses[net['name']],
                                    used_by="%s-%s" % (component_name, '-cluster'),
                                    host=s['name'], net_name=net_name)
                                net_group = network_groups[net['network-group']]
                                net_suffix = net_group.get('hostname-suffix',
                                                           net['network-group'])
                                alias = "%s-%s-%s-%s" % (hostname_prefix,
                                                         cluster['name'],
                                                         component['mnemonic'],
                                                         net_suffix)
                                self.add_hostname_alias(net, addr, alias)
                                service_ip_data['cluster-ip'] = {'ip_address': addr,
                                                                 'hostname': alias}
                            else:
                                addr = service_ip_data['cluster-ip']['ip_address']

                            if 'service-vips' not in s:
                                s['service-vips'] = {}
                            s['service-vips'][component_name] = addr

        # Build a list of interfaces limited to the ones that need to be configured
        server_ifaces = {}
        for iface in s['interfaces']:
            if iface['networks']:
                server_ifaces[iface['name']] = iface

        s['interfaces'] = server_ifaces

    #
    # Add any auto assigned tags from a component to a network group
    #
    def _add_auto_tags(self, component, net_group):

        for auto_tag in component.get('auto-network-tags', []):
            found = False
            for existing_tag in net_group.get('tags', []):
                if existing_tag['name'] == auto_tag['name']:
                    found = True
                    break

            if not found:
                tag_data = {
                    'name': auto_tag['name'],
                    'values': None,
                    'definition': auto_tag,
                    'component': component['name'],
                    'service': component.get('service', 'foundation')
                }
                net_group['tags'].append(tag_data)

    def get_dependencies(self):
        return []
