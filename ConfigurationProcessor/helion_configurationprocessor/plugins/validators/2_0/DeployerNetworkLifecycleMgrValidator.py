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
import logging
import logging.config

from netaddr import IPNetwork, IPAddress, AddrFormatError
from helion_configurationprocessor.cp.model.ValidatorPlugin \
    import ValidatorPlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class DeployerNetworkLifecycleMgrValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(DeployerNetworkLifecycleMgrValidator, self).__init__(
            2.0, instructions, config_files,
            'deployer-network-lifecycle-mgr-2.0')
        self._valid = True
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())

        self._load_inputs()

        # Build lists of components
        component_all_servers = []
        component_on_server_network = []
        component_on_server = []
        for component_name, component in self._service_components.iteritems():
            if component.get('must-be-on-all-servers', False):
                component_all_servers.append(component_name)
            if component.get('must-be-on-server-network', False):
                component_on_server_network.append(component_name)
            if component.get('must-be-on-a-server', False):
                component_on_server.append(component_name)

        # Check control plane definitions
        self._validate_control_planes(component_all_servers, component_on_server)

        # Check servers
        self._validate_servers(component_on_server_network)

    def _load_inputs(self):
        version = float(self.version())
        self._service_components = self._get_dict_from_config_value(version, 'service-components')
        self._control_planes = self._get_dict_from_config_value(version, 'control-planes')
        self._server_roles = self._get_dict_from_config_value(version, 'server-roles')
        self._iface_models = self._get_dict_from_config_value(version, 'interface-models')
        self._network_groups = self._get_dict_from_config_value(version, 'network-groups')
        self._networks = self._get_dict_from_config_value(version, 'networks')
        self._bm_servers = self._get_config_value(version, 'servers')

    def _validate_control_planes(self, component_all_servers, component_on_server):

        for cp_name, cp in self._control_planes.iteritems():
            for component in component_all_servers:
                if component not in cp['common-service-components']:
                    for cluster in cp['clusters']:
                        if component not in cluster['service-components']:
                            msg = ("Control plane %s doesn't have %s "
                                   % (cp_name, component) + "role for all control nodes")
                            self.add_error(msg)
                            self._valid = False
                            continue
                    for resources in cp.get('resources', cp.get('resource-nodes', [])):
                        if component not in resources['service-components']:
                            msg = ("Control plane %s doesn't have %s "
                                   % (cp_name, component) + "role for all resource nodes")
                            self.add_error(msg)
                            self._valid = False
                            continue
        for component in component_on_server:
            found = False
            for cp_name, cp in self._control_planes.iteritems():
                for cluster in cp['clusters']:
                    if component in cluster['service-components']:
                        found = True
                        break
                if not found:
                    for resources in cp.get('resources', cp.get('resource-nodes', [])):
                        if component in resources['service-components']:
                            found = True
                            break
            if not found:
                msg = ("Component %s not on at least one server."
                       % (component))
                self.add_error(msg)
                self._valid = False

    def _validate_servers(self, component_on_server_network):
        for s in self._bm_servers:
            self._validate_server_network(s)
#            s_net_group = self._validate_server_network(s)
#            if s_net_group:
#                for component in component_on_server_network:
#                    component_net_group = self._net_grp_for_component(component)
#                    from pprint import pprint
#                    pprint (self._network_groups[component_net_group])
#                    if (component_net_group != s_net_group
#                            and component_net_group not in self._network_groups[s_net_group].get('routes', [])):
#                        msg = ("The address of server %s must be in a network in the "
#                               % s['id'] + "same network group %s " % component_net_group +
#                               "that has the endpoint for component %s" % component)
#                        self.add_error(msg)
#                        self._valid = False

    def _validate_server_network(self, s):
        # Find network that contains server address
        network = self._network_from_address(s)
        if not network:
            msg = ("Address %s of server %s does not belong to a network in the model"
                   % (s['ip-addr'], s['id']))
            self.add_error(msg)
            self._valid = False
            return None
        # Check if network is tagged or not
        self._check_for_tagged_network(s, network)
        # Find network group of this network, check that it is in
        # interface model of server
        s_int_model, s_network_group = self._check_server_interface(s, network)
        if not s_network_group:
            msg = ("Address %s of server %s is part of network %s " % (s['ip-addr'], s['id'], network) +
                   "but that network is not a member of a network group in its interface model %s"
                   % s_int_model)
            self.add_error(msg)
            self._valid = False
            return None
        else:
            return s_network_group

    def _net_grp_for_component(self, component):
        def_net_grp = None
        for net_name, net_grp in self._network_groups.iteritems():
            endpoints = []
            if 'component-endpoints' in net_grp:
                endpoints += net_grp['component-endpoints']
            if 'tls-component-endpoints' in net_grp:
                endpoints += net_grp['tls-component-endpoints']
            if component in endpoints:
                return net_grp['name']
            elif 'default' in endpoints:
                def_net_grp = net_grp['name']
        return def_net_grp

    def _network_from_address(self, s):
        for net_name, net in self._networks.iteritems():
            if 'cidr' in net:
                ip_net = IPNetwork(unicode(net['cidr']))
                net_start = ip_net[1]
                net_end = ip_net[-2]

                if 'start-address' in net:
                    net_start = IPAddress(net['start-address'])

                if 'end-address' in net:
                    net_end = IPAddress(net['end-address'])

                try:
                    server_ip = IPAddress(s['ip-addr'])
                except AddrFormatError:
                    return None
                else:
                    if net_start <= server_ip <= net_end:
                        return net_name
        return None

    def _check_server_interface(self, s, network):
        net_group = self._networks[network]['network-group']
        s_int_model = self._server_roles[s['role']]['interface-model']
        interfaces = self._iface_models[s_int_model].get('network-interfaces', [])

        for interface in interfaces:
            iface_net_groups = interface.get('network-groups', []) +\
                interface.get('forced-network-groups', [])
            if net_group in iface_net_groups:
                return (s_int_model, net_group)
        return (s_int_model, None)

    def _check_for_tagged_network(self, s, network):
        # Only have to make this check if we will PXE boot the server
        if 'ilo-ip' not in s:
            return

        if self._networks[network].get('tagged-vlan', True):
            msg = ("Possible PXE boot on tagged VLAN\n"
                   "    Network %s includes the address of one or more servers "
                   "that also have iLO values, but is a tagged VLAN.  PXE Booting "
                   "on a tagged VLAN needs specific BIOS support."
                   % (network))
            self.add_warning(msg)
            self._valid = False

    @property
    def instructions(self):
        return self._instructions

    def get_dependencies(self):
        return ['disk-model-2.0',
                'interface-models-2.0',
                'network-groups-2.0',
                'networks-2.0',
                'server-roles-2.0',
                'server-groups-2.0',
                'servers-2.0',
                'control-planes-2.0',
                'nic-mappings-2.0',
                'pass-through-2.0',
                'firewall-rules-2.0',
                'cross-reference-2.0']
