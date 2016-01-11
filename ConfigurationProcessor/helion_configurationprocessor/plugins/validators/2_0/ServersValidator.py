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

from helion_configurationprocessor.cp.model.ValidatorPlugin \
    import ValidatorPlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog

from netaddr import IPNetwork, IPAddress, AddrFormatError
import re

LOG = logging.getLogger(__name__)


class ServersValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(ServersValidator, self).__init__(
            2.0, instructions, config_files,
            'servers-2.0')
        self._valid = True
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())
        version = float(self.version())

        input = self._create_content(version, "servers")
        schema_valid = self.validate_schema(input, "server")
        if schema_valid:
            servers = input.get('servers', [])
            baremetal = {}
            try:
                baremetal = self._create_content(version, 'baremetal')['baremetal'][0]
            except TypeError:
                try:
                    # baremetal_networks is still suppoted for backwards compatibility
                    baremetal = self._create_content(version, 'baremetal_network')['baremetal_network'][0]
                except TypeError:
                    # Possible to have servers with no baremetal section if not using
                    # cobbler to deploy
                    pass

            nic_mappings = self._get_dict_from_config_value(version, 'nic-mappings')
            iface_models = self._get_dict_from_config_value(version, 'interface-models')
            server_roles = self._get_dict_from_config_value(version, 'server-roles')
            server_groups = self._get_dict_from_config_value(version, 'server-groups')

            if baremetal:
                self._validate_baremetal_net(baremetal)
            self._validate_unique_ids(servers)
            self._validate_ip_addresses(servers)
            self._validate_mac_addresses(servers)
            self._validate_server_groups(servers, server_groups)
            self._validate_net_devices(servers, nic_mappings, server_roles, iface_models)

        LOG.info('%s()' % KenLog.fcn())
        return self._valid

    def _validate_unique_ids(self, servers):
        id_set = {}
        for s in servers:
            if s['id'] in id_set:
                id_set[s['id']].append(s['ip-addr'])
                msg = ("Duplicate server id: %s (%s)" %
                       (s['id'], id_set[s['id']]))
                self.add_error(msg)
                self._valid = False
            else:
                id_set[s['id']] = [s['ip-addr']]

    def _validate_baremetal_net(self, baremetal):
        try:
            IPNetwork(baremetal['subnet'])
        except AddrFormatError:
            msg = ("Invalid baremetal subnet: %s" % baremetal['subnet'])
            self.add_error(msg)
            self._valid = False

        try:
            IPNetwork(baremetal['netmask'])
        except AddrFormatError:
            msg = ("Invalid baremetal netmask: %s" % baremetal['netmask'])
            self.add_error(msg)
            self._valid = False

    def _validate_ip_addresses(self, servers):
        for server in servers:
            try:
                IPAddress(server['ip-addr'])
            except AddrFormatError:
                msg = ("Server '%s' has an invalid IP address for 'ip-addr': %s" %
                       (server['id'], server['ip-addr']))
                self.add_error(msg)
                self._valid = False

            if 'ilo-ip' in server:
                try:
                    IPAddress(server['ilo-ip'])
                except AddrFormatError:
                    msg = ("Server '%s' has an invalid IP address for 'ilo-ip': %s" %
                           (server['id'], server['ilo-ip']))
                    self.add_error(msg)
                    self._valid = False

    def _validate_mac_addresses(self, servers):
        mac_addr_regex = r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$'
        for server in servers:
            if 'mac-addr' in server:
                if not re.match(mac_addr_regex, server['mac-addr'].lower()):
                    msg = ("Server '%s' has an invalid MAC address: '%s'. "
                           "Here is an example format: "
                           "'01:23:45:67:89:ab'" %
                           (server['id'], server['mac-addr']))
                    self.add_error(msg)
                    self._valid = False

    def _validate_server_groups(self, servers, server_groups):

        for s in servers:
            if 'server-group' in s:
                if s['server-group'] not in server_groups:
                    msg = ("Server Group '%s' used by server %s "
                           "is not defined" % (s['server-group'], s['id']))
                    self.add_error(msg)
                    self._valid = False

    def _validate_net_devices(self, servers, nic_mappings, server_roles, iface_models):

        for s in servers:
            s_role = server_roles.get(s['role'], {})
            if not s_role:
                msg = ("Server role '%s' used by server %s "
                       "is not defined" % (s['role'], s['id']))
                self.add_error(msg)
                self._valid = False
                continue

            s_iface_model = iface_models.get(s_role['interface-model'], {})
            if not s_iface_model:
                msg = ("Interface model '%s' referenced in server role '%s' "
                       "is not defined" %
                       (s_role['interface-model'], s_role['name']))
                self.add_error(msg)
                self._valid = False

            # We can only validate the device if we have a NIC mapping
            if 'nic-mapping' not in s:
                continue

            s_nic_map = nic_mappings.get(s['nic-mapping'], {})
            if not s_nic_map:
                msg = ("NIC Mapping '%s' used by server %s "
                       "is not defined" % (s['nic-mapping'], s['ip-addr']))
                self.add_error(msg)
                self._valid = False
                continue

            for iface in s_iface_model.get('network-interfaces', []):
                devices = []
                nic_devices = []
                if 'bond-data' in iface:
                    for bond_dev in iface['bond-data']['devices']:
                        devices.append(bond_dev['name'])
                else:
                    devices.append(iface['device']['name'])

                for port in s_nic_map['physical-ports']:
                    nic_devices.append(port['logical-name'])

                for device in devices:
                    if device not in nic_devices:
                        msg = ("Server %s needs device %s for interface %s "
                               "in interface model %s, but this device is "
                               "not defined in its nic-mapping %s." %
                               (s['id'], device, iface['name'],
                                s_iface_model['name'], s_nic_map['name']))
                        self.add_error(msg)
                        self._valid = False

    @property
    def instructions(self):
        return self._instructions

    def get_dependencies(self):
        return ['nic-mappings-2.0',
                'interface-models-2.0',
                'server-roles-2.0',
                'server-groups-2.0']
