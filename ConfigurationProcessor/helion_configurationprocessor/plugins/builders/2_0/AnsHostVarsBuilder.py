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
import netaddr
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
from helion_configurationprocessor.cp.lib.DataTransformer \
    import DataTransformer


LOG = logging.getLogger(__name__)


class AnsHostVarsBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(AnsHostVarsBuilder, self).__init__(
            2.0, instructions, models, controllers,
            'ans-host-vars-2.0')
        LOG.info('%s()' % KenLog.fcn())
        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions, self.cloud_desc)
        self._file_path = os.path.join(self._file_path, 'ansible')

        self._cloud_model = self._models['CloudModel']
        self._cloud_version = CloudModel.version(self._cloud_model, self._version)
        self._cloud_internal = CloudModel.internal(self._cloud_model)

        self._cloud_firewall = {}

    def build(self):
        LOG.info('%s()' % KenLog.fcn())
        cloud_name = CloudDescription.get_cloud_name(self.cloud_desc)
        ntp_servers = CloudModel.get(self._cloud_internal, 'ntp_servers')
        dns_settings = CloudModel.get(self._cloud_internal, 'dns_settings')
        smtp_settings = CloudModel.get(self._cloud_internal, 'smtp_settings')
        control_planes = CloudModel.get(self._cloud_internal, 'control-planes')
        net_group_firewall = CloudModel.get(self._cloud_internal, 'net-group-firewall')
        firewall_settings = CloudModel.get(self._cloud_internal, 'firewall_settings')
        pass_through = CloudModel.get(self._cloud_internal, 'pass_through')
        components = CloudModel.get(self._cloud_internal, 'components')
        services = CloudModel.get(self._cloud_internal, 'services')

        for cp_name, cp in control_planes.iteritems():
            for cluster in cp['clusters']:
                for s in cluster['servers']:
                    self._build_ansible_host_vars(cloud_name, s, cp['endpoints'],
                                                  cp, cluster['name'],
                                                  ntp_servers, dns_settings, smtp_settings,
                                                  pass_through, components, services,
                                                  net_group_firewall, firewall_settings)

            for r_name, resources in cp.get('resources', {}).iteritems():
                for s in resources['servers']:
                    self._build_ansible_host_vars(cloud_name, s, cp['endpoints'],
                                                  cp, resources['name'],
                                                  ntp_servers, dns_settings, smtp_settings,
                                                  pass_through, components, services,
                                                  net_group_firewall, firewall_settings)

        CloudModel.put(self._cloud_internal, 'cloud-firewall', self._cloud_firewall)

    def _build_ansible_host_vars(self, cloud_name, server, cp_endpoints, cp, cluster_name,
                                 ntp_servers=[], dns_settings={}, smtp_settings={}, pass_through={},
                                 components={}, services={},
                                 net_group_firewall={}, firewall_settings={}):
        LOG.info('%s()' % KenLog.fcn())

        components = CloudModel.get(self._cloud_internal, 'components')
        components_by_mnemonic = CloudModel.get(self._cloud_internal, 'components_by_mnemonic')
        filename = "%s/host_vars/%s" % (self._file_path, server['hostname'])
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        self.add_artifact(filename, ArtifactMode.CREATED)

        for if_name, if_data in server['interfaces'].iteritems():
            for net_name, net_data in if_data['networks'].iteritems():
                if net_data.get('hostname') == server['hostname']:
                    my_addr = net_data['addr']

        host_vars = {
            'host': {
                'vars': {
                    'member_id': server.get('member_id', 'cpn'),
                    'my_network_address': my_addr,
                    'my_network_name': server['hostname'],
                    'my_network_interfaces': {}
                },
                'bind': {},
                'tls_in': [],
                'tls_out': [],
                'my_id': server['id'],
                'pass_through': pass_through['servers'].get(server['id'], {}),
                'my_service_ips': {},
                'failure_zone': server.get('failure-zone'),
                'role': server.get('role'),
                'my_dimensions': {
                    'cloud_name': cloud_name,
                    'hostname': server['hostname'],
                    'cluster': cluster_name,
                    'control_plane': cp['name']
                },
                'my_logical_volumes': {},
                'my_device_groups': {}
            },
            'ntp_servers': ntp_servers,
            'dns': dns_settings,
            'smtp': smtp_settings,
        }

        nic_mapping = {}
        if server.get('nic_map', {}):
            nic_mapping['nic_mappings'] = []
            for dev in server['nic_map']['physical-ports']:
                nic_map = {'logical_name': dev['logical-name'],
                           'bus_address': dev['bus-address'],
                           'type': dev['type']}
                if 'port-attributes' in dev:
                    nic_map['port_attributes'] = {}
                    for key, val in dev['port-attributes'].iteritems():
                        new_key = key.replace('-', '_')
                        nic_map['port_attributes'][new_key] = str(val)
                nic_mapping['nic_mappings'].append(nic_map)

        #
        #  Add per-service ips if they exist
        #
        if 'service-ips' in server:
            host_vars['host']['my_service_ips'] = server['service-ips']

        #
        #  Add list of bind addresses
        #
        for component_name, endpoint_data in cp_endpoints.iteritems():
            if component_name in server['components']:
                mnemonic = components[component_name]['mnemonic'].replace('-', '_')

                if mnemonic not in host_vars['host']['bind']:
                    host_vars['host']['bind'][mnemonic] = {}

                for role, role_data in endpoint_data.iteritems():
                    for data in role_data:
                        if 'address' in data['bind']:
                            bind_address = data['bind']['address']
                        else:
                            # May have to map to a network
                            for if_name, if_data in server['interfaces'].iteritems():
                                for net_name, net_data in if_data['networks'].iteritems():
                                    if data['bind']['network_group'] == net_data['network-group']:
                                        bind_address = net_data['addr']
                                        break
                        bind_port = data['bind']['port']
                        host_vars['host']['bind'][mnemonic][role] = {'ip_address': bind_address,
                                                                     'port': bind_port}

        #
        # Add list of tls terminations
        #
        for component_name, endpoint_data in cp_endpoints.iteritems():
            if component_name in server['components']:
                for role, role_data in endpoint_data.iteritems():
                    for data in role_data:

                        if 'tls-term'in data:
                            # Find the addesss in the right group
                            accept_addr = None
                            for if_name, if_data in server['interfaces'].iteritems():
                                for net_name, net_data in if_data['networks'].iteritems():
                                    if data['tls-term']['network_group'] == net_data['network-group']:
                                        accept_addr = net_data['addr']
                                        break

                            if not accept_addr:
                                msg = ("Can't find address in Net Group %s on %s when "
                                       "configuring tls for %s port %s" %
                                       (data['tls-term']['network_group'], server['name'],
                                        component_name, data['tls-term']['port']))
                                self.add_error(msg)

                            accept = {'ip_address': accept_addr,
                                      'port': data['tls-term']['port']}
                            connect = {'ip_address': data['bind']['address'],
                                       'port': data['bind']['port']}
                            term = {'name': component_name,
                                    'role': role,
                                    'accept': accept,
                                    'connect': connect}
                            host_vars['host']['tls_in'].append(term)

        #
        # Add a list of tls initiations
        #
        #  Build a list of all consumed services from this host
        consumed = set()
        for component_name in server['components']:
            if component_name not in components:
                print "Warning: No data for %s when buiding tls list" % component_name
                continue

            component_data = components[component_name]
            for consumes in component_data.get('consumes-services', []):
                consumed.add(consumes['service-name'])

        for consumed_service in consumed:
            service_name = components_by_mnemonic[consumed_service]['name']
            if service_name in cp_endpoints:
                endpoint_data = cp_endpoints[service_name]
                for role, role_data in endpoint_data.iteritems():
                    for data in role_data:
                        if 'tls-init'in data:
                            accept = {'ip_address': data['access']['address'],
                                      'host': data['access']['hostname'],
                                      'port': data['access']['port']}
                            connect = {'ip_address': data['tls-init']['address'],
                                       'host': data['tls-init']['hostname'],
                                       'port': data['tls-init']['port']}
                            init = {'name': service_name,
                                    'role': role,
                                    'accept': accept,
                                    'connect': connect}
                            host_vars['host']['tls_out'].append(init)

        #
        # Add Disk info
        #
        disk_model = DataTransformer(server['disk-model']).all_output('-', '_')
        host_vars['host']['my_disk_models'] = disk_model

        #
        # Add a list of logical volumes by consuming component. Makes it
        # possible for a service to find its mountpoint
        #
        for vg in disk_model.get('volume_groups', []):
            for lv in vg.get('logical_volumes', []):
                if 'consumer' in lv:
                    component_name = lv['consumer'].get('name')
                    if not component_name:
                        msg = ("Consumer attribute on %s:%s in "
                               "disk-model %s does not have a 'name' value ." %
                               (vg['name'], lv['name'], disk_model['name']))
                        self.add_error(msg)
                        continue

                    elif component_name not in components:
                        # Make this a warning, as it could be the customer is passing this
                        # to some playbook we don't know about
                        msg = ("Unknown component '%s'as consumer of "
                               "%s:%s in disk-model %s." %
                               (component_name, vg['name'], lv['name'], disk_model['name']))
                        self.add_warning(msg)
                        mnemonic = component_name

                    else:
                        if component_name not in server['components']:
                            msg = ("Server %s (%s) uses disk-model %s which includes a logical "
                                   "volume to be consumed by '%s', but that component does not "
                                   "run on this server." %
                                   (server['id'], server['hostname'], disk_model['name'],
                                    component_name))
                            self.add_warning(msg)

                        mnemonic = components[component_name]['mnemonic'].replace('-', '_')

                    if mnemonic not in host_vars['host']['my_logical_volumes']:
                        host_vars['host']['my_logical_volumes'][mnemonic] = []

                    host_vars['host']['my_logical_volumes'][mnemonic].append(deepcopy(lv))

        #
        # Add a list of device-groups volumes by consumer
        #
        for device_group in disk_model.get('device_groups', []):
            if 'consumer' in device_group:
                consumer_name = device_group['consumer'].get('name')
                if not consumer_name:
                    msg = ("Consumer attribute on device-group %s in "
                           "disk-model %s does not have a 'name' value ." %
                           (device_group['name'], disk_model['name']))
                    self.add_error(msg)
                    continue

                elif consumer_name not in services and consumer_name not in components:
                    msg = ("Unknown consumer '%s' of device-group %s"
                           "in disk-model %s." %
                           (consumer_name, device_group['name'], disk_model['name']))
                    self.add_warning(msg)

                elif consumer_name not in server['services'] and consumer_name not in server['components']:
                    msg = ("Server %s (%s) uses disk-model %s which includes a device-group "
                           "be consumed by '%s', but there are no components of that service "
                           "on this server." %
                           (server['id'], server['hostname'], disk_model['name'],
                            consumer_name))
                    self.add_warning(msg)

                if consumer_name not in host_vars['host']['my_device_groups']:
                    host_vars['host']['my_device_groups'][consumer_name] = []

                host_vars['host']['my_device_groups'][consumer_name].append(deepcopy(device_group))

        #
        # Generate os-config network data
        #
        # create network_interface role compatible host_vars
        (service_tags, ovs_bridge_host_vars, vlan_host_vars,
         bond_host_vars, ether_host_vars, net_group_dict) = self._build_network_host_vars(server)
        host_vars['host']['my_network_tags'] = service_tags

        #
        # Generate a structure to tell keepalived what device to bind vips to.
        # Although this is really a group thing, we have to do this in here as
        # we don't have the device info anywhere else
        #
        net_iface_vars = {}
        for vip_net_name, vip_net_data in cp['vip_networks'].iteritems():
            #
            # Build a list of all VIPs on this network
            #
            vips = set()
            for vip_data in vip_net_data:
                if vip_data['provider'] in server['components']:
                    vips.add(vip_data['address'])

            # Find the device for this network from the networkd groups
            device = None
            for ng_name, ng_data in net_group_dict.items():
                for net in ng_data.get('networks', []):
                    if net['name'] == vip_net_name:
                        device = ng_data['device']
                        break

            if device:
                for vip in vips:
                    device_data = {'device': device,
                                   'interface': vip_net_name,
                                   'vip_address': vip}
                    if 'network_interfaces' not in net_iface_vars:
                        net_iface_vars['network_interfaces'] = []
                    net_iface_vars['network_interfaces'].append(device_data)

        self.add_vips_to_network_host_vars(net_iface_vars, bond_host_vars,
                                           ether_host_vars, ovs_bridge_host_vars,
                                           vlan_host_vars)

        # Get server firewall settings
        host_vars['firewall'] = self.getFirewall(server, cp, net_group_firewall, firewall_settings,
                                                 net_group_dict)

        # Save the firewall settings for this server
        self._cloud_firewall[server['name']] = host_vars['firewall']

        with open(filename, 'w') as fp:
            yaml.dump(host_vars, fp, default_flow_style=False, indent=4)
            if ovs_bridge_host_vars['ovs_bridge_interfaces']:
                yaml.dump(ovs_bridge_host_vars, fp, default_flow_style=False, indent=4)
            if vlan_host_vars['network_vlan_interfaces']:
                yaml.dump(vlan_host_vars, fp, default_flow_style=False, indent=4)
            if bond_host_vars['network_bond_interfaces']:
                yaml.dump(bond_host_vars, fp, default_flow_style=False, indent=4)
            if ether_host_vars['network_ether_interfaces']:
                yaml.dump(ether_host_vars, fp, default_flow_style=False, indent=4)
            if nic_mapping:
                # Have to set default_style to ensure the bus address is in quotes
                yaml.dump(nic_mapping, fp, default_style='\'', default_flow_style=False, indent=4)
            if net_iface_vars:
                yaml.dump(net_iface_vars, fp, default_flow_style=False, indent=4)

    def add_vips_to_network_host_vars(self, net_iface_vars, bond_host_vars,
                                      ether_host_vars, ovs_bridge_host_vars,
                                      vlan_host_vars):
        #
        # Modify the network host vars to add in a list of vips on each
        # interface so that we can add routing rules for them.
        #
        devices_to_vips = {}
        for iface in net_iface_vars.get('network_interfaces', []):
            device = iface['device']
            if device not in devices_to_vips:
                devices_to_vips[device] = set()
            devices_to_vips[device].add(iface['vip_address'])

        for interface in ovs_bridge_host_vars['ovs_bridge_interfaces'] \
                + vlan_host_vars['network_vlan_interfaces'] \
                + bond_host_vars['network_bond_interfaces'] \
                + ether_host_vars['network_ether_interfaces']:
            if interface['device'] in devices_to_vips:
                interface['vips'] = list(devices_to_vips[interface['device']])

    def _cidr_to_mask(self, cidr):

        mask = int(str.split(cidr, '/')[1])
        bits = 0
        for i in xrange(32 - mask, 32):
            bits |= (1 << i)
        return "%d.%d.%d.%d" % ((bits & 0xff000000) >> 24,
                                (bits & 0xff0000) >> 16,
                                (bits & 0xff00) >> 8,
                                (bits & 0xff))

    def _build_network_host_vars(self, server):
        server_bond_dictionary = {}
        server_ether_dictionary = {}
        server_vlan_dictionary = {}
        server_ovs_bridge_dictionary = {}
        server_service_tags_list = []
        server_network_groups_dict = {}
        server_bond_dictionary['network_bond_interfaces'] = []
        server_ether_dictionary['network_ether_interfaces'] = []
        server_vlan_dictionary['network_vlan_interfaces'] = []
        server_ovs_bridge_dictionary['ovs_bridge_interfaces'] = []

        # get all the interfaces on this server
        interfaces = server.get('interfaces', None)
        for interface, interface_attrs in interfaces.items():
            # get the bond data for this interface
            bond_data = interface_attrs.get('bond-data', None)
            bond_dictionary = {}
            # get the ports
            ports = self.getPorts(bond_data)
            # get the device definition
            interface_name = self.getInterfaceName(interface_attrs.get('device', None))

            # The existence of bond_data indicates that this is a bonded interface
            if bond_data:
                bond_dictionary['device'] = interface_name
                bond_dictionary['route'] = []
                bond_dictionary['bond_slaves'] = []
                bond_options = bond_data.get('options', None)
                # lose 'bond-' prefix from any existing option keys
                bond_options = self.migrateBondOptions(bond_options)
                # promote some options
                bond_mode = bond_options.pop('mode', None)
                bond_primary = bond_options.pop('primary', None)
                if bond_mode:
                    bond_dictionary['bond_mode'] = bond_mode
                for port in ports:
                    bond_dictionary['bond_slaves'].append(port)
                if bond_primary:
                    bond_dictionary['bond_primary'] = bond_primary
                if bond_options:
                    bond_dictionary['bond_options'] = bond_options

            # get all networks on this interface
            networks = interface_attrs.get('networks', None)
            for network_name, network_attrs in networks.items():
                addr = network_attrs.get('addr', None)
                gateway_ip = network_attrs.get('gateway-ip', None)
                tagged_vlan = network_attrs.get('tagged-vlan', True)
                vlanid = network_attrs.get('vlanid', None)
                routes = network_attrs.get('routes', None)
                service_tags = network_attrs.get('service-tags', None)
                # use service tags to determine if a bridge is needed
                needs_bridge = self.getBridgeInfo(service_tags)
                # the interface on which to add the bridge will get determined later as
                # we build the interfaces
                bridge_interface = ''

                if bond_data:
                    if not tagged_vlan:
                        bond_dictionary['route'] = []
                        intf_route_list = self.getRoutes(routes, gateway_ip)
                        if needs_bridge:
                            bridge_interface = interface_name
                            bond_dictionary['ovs_bridge'] = self.getBridgeName(bridge_interface)
                        else:
                            network_group_device = bond_dictionary['device']
                            # set address and bootproto to static
                            self.getInterfaceInfo(bond_dictionary, network_attrs)
                            bond_dictionary['route'].extend(intf_route_list)
                            bond_service_tag_dict = {}
                            bond_service_tag_dict['tags'] = self.getServiceTags(service_tags)
                            # save service tag info if a tag exists
                            if bond_service_tag_dict.get('tags', None):
                                bond_service_tag_dict['address'] = addr
                                bond_service_tag_dict['network'] = network_name
                                bond_service_tag_dict['device'] = interface_name
                                server_service_tags_list.append(bond_service_tag_dict)

                # set attributes for vlan interface
                if tagged_vlan:
                    vlan_dictionary = {}
                    vlan_service_tag_dict = {}
                    vlan_service_tag_dict['tags'] = self.getServiceTags(service_tags)
                    vlan_service_tag_dict['network'] = network_name
                    vlan_dictionary['vlanid'] = vlanid
                    vlan_device = 'vlan' + str(vlanid)
                    vlan_dictionary['device'] = vlan_device
                    vlan_service_tag_dict['device'] = vlan_device
                    vlan_dictionary['vlanrawdevice'] = interface_name
                    vlan_dictionary['route'] = []
                    intf_route_list = self.getRoutes(routes, gateway_ip)
                    if needs_bridge:
                        bridge_interface = vlan_device
                        vlan_dictionary['bootproto'] = self.getBootProto("")
                        vlan_dictionary['ovs_bridge'] = self.getBridgeName(bridge_interface)
                    else:
                        network_group_device = vlan_dictionary['device']
                        self.getInterfaceInfo(vlan_dictionary, network_attrs)
                        vlan_dictionary['route'].extend(intf_route_list)
                        vlan_service_tag_dict['address'] = addr
                        # save service tag info if a tag exists
                        if vlan_service_tag_dict.get('tags', None):
                            server_service_tags_list.append(vlan_service_tag_dict)
                    # clean out any null values
                    vlan_dict_clean = {k: v for k, v in vlan_dictionary.items() if v}
                    server_vlan_dictionary['network_vlan_interfaces'].append(vlan_dict_clean)
                elif not tagged_vlan and not bond_data:
                    ether_dictionary = {}
                    ether_service_tag_dict = {}
                    ether_service_tag_dict['tags'] = self.getServiceTags(service_tags)
                    ether_service_tag_dict['network'] = network_name
                    ether_dictionary['device'] = interface_name
                    ether_service_tag_dict['device'] = interface_name
                    ether_dictionary['route'] = []
                    intf_route_list = self.getRoutes(routes, gateway_ip)
                    if needs_bridge:
                        bridge_interface = interface_name
                        ether_dictionary['bootproto'] = self.getBootProto("")
                        ether_dictionary['ovs_bridge'] = self.getBridgeName(bridge_interface)
                    else:
                        network_group_device = ether_dictionary['device']
                        self.getInterfaceInfo(ether_dictionary, network_attrs)
                        ether_dictionary['route'].extend(intf_route_list)
                        ether_service_tag_dict['address'] = addr
                        # save service tag info if a tag exists
                        if ether_service_tag_dict.get('tags', None):
                            server_service_tags_list.append(ether_service_tag_dict)
                    # clean out any null values
                    ether_dict_clean = {k: v for k, v in ether_dictionary.items() if v}
                    server_ether_dictionary['network_ether_interfaces'].append(ether_dict_clean)

                # set attributes for a bridge
                if needs_bridge:
                    ovsbr_dictionary = {}
                    ovsbr_service_tag_dict = {}
                    ovsbr_service_tag_dict['tags'] = self.getServiceTags(service_tags)
                    ovsbr_service_tag_dict['network'] = network_name
                    network_group_device = self.getBridgeName(bridge_interface)
                    ovsbr_dictionary['device'] = network_group_device
                    ovsbr_service_tag_dict['device'] = network_group_device
                    self.getInterfaceInfo(ovsbr_dictionary, network_attrs)
                    ovsbr_service_tag_dict['address'] = addr
                    ovsbr_dictionary['port'] = bridge_interface
                    ovsbr_service_tag_dict['bridge_port'] = bridge_interface
                    ovsbr_dictionary['route'] = intf_route_list
                    # TODO where does hwaddr come from and do we even need this ?
                    ovsbr_dictionary['hwaddr'] = ''
                    # clean out any null values
                    ovsbr_dict_clean = {k: v for k, v in ovsbr_dictionary.items() if v}
                    server_ovs_bridge_dictionary['ovs_bridge_interfaces'].append(ovsbr_dict_clean)
                    # save service tag info if a tag exists
                    if ovsbr_service_tag_dict.get('tags', None):
                        server_service_tags_list.append(ovsbr_service_tag_dict)

                # add to server network groups
                self.getNetworkByGroup(server_network_groups_dict, network_name,
                                       network_group_device, network_attrs)

            if bond_data:
                if 'bootproto' not in bond_dictionary:
                    bond_dictionary['bootproto'] = self.getBootProto("")
                # clean out any null values
                bond_dict_clean = {k: v for k, v in bond_dictionary.items() if v}
                server_bond_dictionary['network_bond_interfaces'].append(bond_dict_clean)

        return (server_service_tags_list, server_ovs_bridge_dictionary,
                server_vlan_dictionary, server_bond_dictionary,
                server_ether_dictionary, server_network_groups_dict)

    def getInterfaceInfo(self, interface_dict, network_attrs):
        addr = network_attrs.get('addr', None)
        cidr = network_attrs.get('cidr', None)
        interface_dict['address'] = addr
        interface_dict['bootproto'] = self.getBootProto(addr)
        interface_dict['cidr'] = cidr
        interface_dict['netmask'] = self.getNetmask(cidr)
        interface_dict['gateway'] = network_attrs.get('gateway-ip', None)
        interface_dict['routing_table'] = network_attrs.get('network-group', None)

    def getRoutes(self, routes, gateway_ip):
        route_list = []
        for route in routes:
            rte_network, rte_netmask, rte_gateway = self.getRouteInfo(route, gateway_ip)
            route_dictionary = {}
            route_dictionary['network'] = rte_network
            route_dictionary['netmask'] = rte_netmask
            route_dictionary['gateway'] = rte_gateway
            route_list.append(route_dictionary)
        return route_list

    def getNetworkByGroup(self, network_groups_dict, network_name, device_name, network_attrs):
        # for each network, put it into the desired network group.
        network_group = network_attrs.get('network-group', None)
        addr = network_attrs.get('addr', None)
        cidr = network_attrs.get('cidr', None)
        gateway_ip = network_attrs.get('gateway-ip', None)
        if network_group not in network_groups_dict.keys():
            network_groups_dict[network_group] = {}
            network_groups_dict[network_group]['name'] = network_group
            network_groups_dict[network_group]['networks'] = []
        network_groups_dict[network_group]['device'] = device_name
        if addr:
            network_groups_dict[network_group]['address'] = addr
        if cidr:
            network_dict = {}
            network_dict['name'] = network_name
            network_dict['cidr'] = cidr
            network_dict['gateway'] = gateway_ip
            network_groups_dict[network_group]['networks'].append(network_dict)

    def getBridgeInfo(self, service_tags):
        needs_bridge = False
        for tag in service_tags:
            # get the definition dictionary from each tag
            definition = tag.get('definition', None)
            if definition:
                needs_bridge = definition.get('needs-bridge', False)
            # Stop as soon as we find a tag that needs a bridge
            if needs_bridge:
                break
        return needs_bridge

    def getBridgeName(self, interface):
        return "br-" + interface

    def getBootProto(self, addr):
        # We don't need to support dhcp
        if addr:
            return 'static'
        else:
            return 'manual'

    def getRouteInfo(self, route, gateway):
        rte_network = ''
        rte_netmask = ''
        if route['default']:
            rte_network = '0.0.0.0'
            rte_netmask = '0.0.0.0'
        else:
            # If route is not 'default',
            ipNetwork = netaddr.IPNetwork(route['cidr'])
            rte_network = str(ipNetwork.network)
            rte_netmask = str(ipNetwork.netmask)
        return rte_network, rte_netmask, gateway

    def migrateBondOptions(self, options):
        # remove 'bond-' prefixes
        prefix = 'bond-'
        migrated_options = options
        for key, value in migrated_options.iteritems():
            if key.startswith(prefix):
                new_key = key[len(prefix):]
                del migrated_options[key]
                migrated_options[new_key] = value

        return migrated_options

    def getNetmask(self, netmask):
        # netmask could be xx.xx.xx.xx or xx.xx.xx.xx/yy
        if netmask and '/' in netmask:
            ip, routing_prefix = netmask.split("/")
            return int(routing_prefix)
        else:
            return netmask

    def getInterfaceName(self, device):
        name = device.get('name', None)
        nic_mapping = device.get('nic-mapping', None)
        if nic_mapping:
            # TODO: do something to map the port to an ethx
            # TODO: don't know how to do this yet
            return name
        else:
            return name

    def getServiceTags(self, service_tags):
        service_tag_list = []
        for tag in service_tags:
            service_tag_dict = {}
            service_tag_dict['tag'] = tag.get('name', None)
            service_tag_dict['service'] = tag.get('service', None)
            service_tag_dict['data_values'] = tag.get('values', None)
            service_tag_dict['component'] = tag.get('component', None)
            service_tag_list.append(service_tag_dict)
        return service_tag_list

    def getPorts(self, bond_data):
        ports = []
        if not bond_data:
            return ports
        devices = bond_data.get('devices', None)
        if not devices:
            return ports

        for device in devices:
            name = device.get('name', None)
            nic_mapping = device.get('nic-mapping', None)
            if nic_mapping:
                # TODO: do something to map the port to an ethx
                # TODO: don't know how to do this yet
                ports.append(name)
            else:
                ports.append(name)
        return ports

    def getFirewall(self, server, cp, net_group_firewall, firewall_settings, net_group_dict):
        #
        # Build a list of firwall rules, indexed by IP
        # address
        #
        firewall = {}
        rules = {}
        managed_networks = []
        load_balancers = cp.get('load-balancers', {})

        # Build a mapping

        # Loop though interfaces adding rules for each component on that interface

        for iface_name, iface_data in server.get('interfaces', {}).iteritems():
            for net_name, net_data in iface_data.get('networks', {}).iteritems():

                if 'addr' not in net_data:
                    continue

                firewall_rules = net_group_firewall.get(net_data['network-group'], {})
                component_rules = firewall_rules.get('component', [])
                user_rules = firewall_rules.get('user', [])
                vips = {}

                # Get the device for this interface
                interface = net_group_dict[net_data['network-group']]['device']

                managed_network = {'name': net_data['network-group'],
                                   'interface': interface}
                managed_networks.append(managed_network)

                # if net_data['addr'] equals server['addr'] then a rule
                # is needed to allow ssh for Ansible since the 'os-install'
                # interface has been 'subsumed' into a Helion managed network
                if net_data['addr'] == server['addr']:
                    if net_data['addr'] not in rules:
                        rules[net_data['addr']] = []
                    ssh_rule = {'type': 'allow',
                                'remote-ip-prefix': '0.0.0.0/0',
                                'port-range-min': 22,
                                'port-range-max': 22,
                                'protocol': 'tcp',
                                'chain': net_data['network-group'],
                                'component': 'ssh'}
                    rules[net_data['addr']].append(ssh_rule)

                for comp_name in net_data['endpoints']:
                    if comp_name in component_rules:
                        addrs = []
                        # If the component has its own IP address then the
                        # ports are associated with that not the server address
                        if comp_name in server.get('service-ips', {}):
                            addrs.append(server['service-ips'][comp_name])
                            if comp_name in server.get('service-vips', {}):
                                addrs.append(server['service-vips'][comp_name])
                        else:
                            addrs.append(net_data['addr'])

                        for addr in addrs:
                            if addr not in rules:
                                rules[addr] = []
                            for firewall_rule in component_rules[comp_name]:
                                firewall_rule['chain'] = net_data['network-group']
                                firewall_rule['component'] = comp_name
                            rules[addr].extend(deepcopy(component_rules[comp_name]))

                    # Check for Load balancers
                    for name, data in load_balancers.get(comp_name, {}).iteritems():
                        for vip in data['networks']:
                            vip_address = vip['ip-address']
                            if vip_address not in rules:
                                rules[vip_address] = []
                                vips[vip_address] = vip

                            vip_rule = {'type': 'allow',
                                        'remote-ip-prefix': '0.0.0.0/0',
                                        'port-range-min': vip['vip-port'],
                                        'port-range-max': vip['vip-port'],
                                        'protocol': 'tcp',
                                        'chain': vip['network-group'],
                                        'component': vip['component-name']}
                            rules[vip_address].append(vip_rule)

                # Add any rules defined by a network tag
                for tag_data in net_data.get('service-tags'):
                    for tag_ep in tag_data['definition'].get('endpoints', []):
                        tag_rule = {'type': 'allow',
                                    'remote-ip-prefix': '0.0.0.0/0',
                                    'port-range-min': tag_ep['port'],
                                    'port-range-max': tag_ep['port'],
                                    'protocol': tag_ep.get('protocol', 'tcp'),
                                    'chain': net_data['network-group'],
                                    'component': tag_data['component']}
                        if net_data['addr'] not in rules:
                            rules[net_data['addr']] = []
                        rules[net_data['addr']].append(tag_rule)

                # Add any user defined rules
                if user_rules:
                    if net_data['addr'] not in rules:
                        rules[net_data['addr']] = []
                    for rule_data in user_rules:
                        user_rule = deepcopy(rule_data)
                        user_rule['chain'] = net_data['network-group']
                        rules[net_data['addr']].append(user_rule)
                        # Make a separate copy as teh vip may be in a different chain
                        for vip, vip_data in vips.iteritems():
                            vip_rule = deepcopy(user_rule)
                            vip_rule['chain'] = vip_data['network-group']
                            rules[vip].append(vip_rule)

        firewall['rules'] = rules
        firewall['managed_networks'] = managed_networks
        firewall['enable'] = firewall_settings.get('enable', True)
        firewall['settings'] = firewall_settings

        return firewall

    def get_dependencies(self):
        return []
