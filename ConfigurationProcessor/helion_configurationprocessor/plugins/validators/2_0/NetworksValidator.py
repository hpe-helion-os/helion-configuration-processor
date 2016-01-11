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

LOG = logging.getLogger(__name__)


class NetworksValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(NetworksValidator, self).__init__(
            2.0, instructions, config_files,
            'networks-2.0')
        self._valid = False
        self._valid_cidr = True
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())
        version = float(self.version())

        input = self._create_content(version, "networks")
        self._valid = self.validate_schema(input, "network")

        if self._valid:
            networks = input.get('networks', [])
            self._validate_names(networks)
            for net in networks:
                self._validate_vlans(net)
                self._validate_cidr(net)
                self._validate_vxlan_net_has_cidr(net)
            if self._valid_cidr:
                self._validate_no_cidr_overlap(networks)
            self._validate_gateways(networks)

        LOG.info('%s()' % KenLog.fcn())
        return self._valid

    def _validate_names(self, networks):

        #
        # Check each model is only defined once
        #
        names = set()
        for net in networks:
            if net['name'] in names:
                msg = ("Network %s is defined more than once." %
                       (net['name']))
                self.add_error(msg)
                self._valid = False
            else:
                names.add(net['name'])

    def _validate_no_cidr_overlap(self, networks):

        #
        # Check no two networks have the same cidr
        #
        cidrs = {}
        overlaps = {}
        for net in networks:
            net_cidr = net.get('cidr')
            if not net_cidr:
                continue

            # Note: this validator run after each cidr has been validated
            ip_net = IPNetwork(unicode(net['cidr']))
            net_start = ip_net[1]
            net_end = ip_net[-2]
            if 'start-address' in net:
                net_start = IPAddress(net['start-address'])
            if 'end-address' in net:
                net_end = IPAddress(net['end-address'])

            cidrs[net['name']] = {'cidr': net['cidr'],
                                  'start': net_start,
                                  'end': net_end}

        for net_name, net in cidrs.iteritems():
            for other_net_name, other_net in cidrs.iteritems():
                if net_name == other_net_name:
                    continue
                net_start = net['start']
                net_end = net['end']
                net_cidr = net['cidr']
                other_net_start = other_net['start']
                other_net_end = other_net['end']
                other_net_cidr = other_net['cidr']

                if ((other_net_start <= net_start <= other_net_end)
                        or (other_net_start <= net_end <= other_net_end)):
                    if net_name not in overlaps:
                        overlaps[net_name] = []
                    overlaps[net_name].append(other_net_name)

                    # check we haven't already reported this the other way round
                    if net_name not in overlaps.get(other_net_name, []):
                        msg = ("Address range of networks %s (%s: %s to %s) "
                               "and %s (%s: %s to %s) overlap." %
                               (net_name, net_cidr, net_start, net_end,
                                other_net_name, other_net_cidr,
                                other_net_start, other_net_end))
                        self.add_error(msg)
                        self._valid = False

    def _validate_cidr(self, net):
        if 'cidr' in net:
            # Find the first and last address of the cidr
            try:
                ip_net = IPNetwork(unicode(net['cidr']))
            except AddrFormatError:
                msg = ("Network %s: %s is not a valid CIDR."
                       % (net['name'], net['cidr']))
                self.add_error(msg)
                self._valid = False
                self._valid_cidr = False
                return
            else:
                if ip_net.size < 4:
                    msg = ("Network %s: CIDR %s range is too small. It must "
                           "have at least 4 IP addresses in its range." %
                           (net['name'], net['cidr']))
                    self.add_error(msg)
                    self._valid = False
                    self._valid_cidr = False
                    return
                cidr_start = ip_net[1]
                cidr_end = ip_net[-2]

            # Check start address is valid
            if 'start-address' in net:
                net_start = IPAddress(net['start-address'])
                if net_start < cidr_start or net_start > cidr_end:
                    msg = ("Network %s: Start address %s is not in "
                           "cidr range %s (%s - %s)" %
                           (net['name'], net_start, net['cidr'],
                            cidr_start, cidr_end))
                    self.add_error(msg)
                    self._valid = False

            # Check end address is valid
            if 'end-address' in net:
                net_end = IPAddress(net['end-address'])
                if net_end < cidr_start or net_end > cidr_end:
                    msg = ("Network %s: End address %s is not in "
                           "cidr range %s (%s - %s)" %
                           (net['name'], net_end, net['cidr'],
                            cidr_start, cidr_end))
                    self.add_error(msg)
                    self._valid = False

            # Check end address is >= start address
            if 'start-address' in net and 'end-address' in net:
                net_start = IPAddress(net['start-address'])
                net_end = IPAddress(net['end-address'])
                if net_end < net_start:
                    msg = ("Network %s: end address %s is less than "
                           "start address %s" %
                           (net['name'], net_end, net_start))
                    self.add_error(msg)
                    self._valid = False

            # Check gateway address is valid
            if 'gateway-ip' in net:
                gateway_ip = IPAddress(net['gateway-ip'])
                if gateway_ip < cidr_start or gateway_ip > cidr_end:
                    msg = ("Network %s: Gateway IP address %s is not in "
                           "cidr range %s (%s - %s)" %
                           (net['name'], gateway_ip, net['cidr'],
                            cidr_start, cidr_end))
                    self.add_error(msg)
                    self._valid = False

    def _validate_vxlan_net_has_cidr(self, net):
        net_vxlan_tag = 'neutron.networks.vxlan'
        if 'cidr' not in net:
            net_group_name = net['network-group']
            if net_group_name in self._get_net_groups_with_tag(net_vxlan_tag):
                msg = ("Network group %s has the tag '%s', but its "
                       "network %s has no CIDR. All networks in a network "
                       "group with the tag '%s' should have a CIDR." %
                       (net_group_name, net_vxlan_tag, net['name'], net_vxlan_tag))
                self.add_error(msg)
                self.valid = False

    def _validate_vlans(self, net):
        version = float(self.version())
        network_groups = self._create_content(version, "network-groups")
        network_groups = network_groups['network-groups']
        net_vlan_tag = 'neutron.networks.vlan'

        if ('vlanid' not in net and (
                'tagged-vlan' not in net or net['tagged-vlan'])):
            msg = ("Network %s: networks are tagged vlans by default, "
                   "but a vlanid was not set. Please set a vlanid for "
                   "this network or set tagged-vlan: false" % (net['name']))
            self.add_error(msg)
            self._valid = False

        vlan_min, vlan_max = (1, 4094)
        if 'vlanid' in net and not (vlan_min <= net['vlanid'] <= vlan_max):
            msg = ("Network %s: the vlan id %s is not valid. "
                   "It should be an integer in the range [%s, %s]."
                   % (net['name'], net['vlanid'], vlan_min, vlan_max))
            self.add_error(msg)
            self._valid = False

        if 'tagged-vlan' not in net or net['tagged-vlan']:
            network_group_name = net['network-group']
            for network_group in network_groups:
                if network_group['name'] == network_group_name and (
                        'tags' in network_group):
                    for tag in network_group['tags']:
                        if tag == net_vlan_tag or (
                                type(tag) is dict and net_vlan_tag in tag):
                            msg = ("Network %s is a tagged vlan, but its "
                                   "network group %s has the tag '%s', making "
                                   "it a provider vlan network. Provider "
                                   "vlans should not be associated with "
                                   "tagged vlan networks." %
                                   (net['name'], network_group_name,
                                    net_vlan_tag))
                            self.add_error(msg)
                            self._valid = False
                            break
                    break

    def _validate_gateways(self, networks):
        version = float(self.version())
        network_group_data = self._create_content(version, "network-groups")
        network_groups = {}
        for grp in network_group_data['network-groups']:
            network_groups[grp['name']] = grp

        # Build a list of how many networks there are in each group
        net_group_counts = {}
        for net in networks:
            if net['network-group'] not in net_group_counts:
                net_group_counts[net['network-group']] = 0
            net_group_counts[net['network-group']] += 1

        for net in networks:

            # Check Group exists
            if net['network-group'] not in network_groups:
                msg = ("Network group %s referenced by network %s "
                       "is not defined" % (net['network-group'], net['name']))
                self.add_error(msg)
                self._valid = False
                return

            net_group = network_groups[net['network-group']]

            # If group has routes check we have gateway
            if 'routes' in net_group and 'gateway-ip' not in net:
                msg = ("Network %s is part of a network group that provides "
                       "routes, but it does not have a 'gateway-ip' value."
                       % (net['name']))
                self.add_error(msg)
                self._valid = False
                continue

            # If there are more than one network in the group then we
            # need the gateway for routing within the group
            if net_group_counts[net['network-group']] > 1 and 'gateway-ip' not in net:
                msg = ("Network %s is part of a network group with more than "
                       "one network, but it does not have a 'gateway-ip' value."
                       % (net['name']))
                self.add_error(msg)
                self._valid = False

    def _get_net_groups_with_tag(self, checked_tag):
        version = float(self.version())
        net_groups = self._create_content(version, "network-groups")
        net_groups = net_groups['network-groups']
        all_net_groups_with_tag = set()

        for net_group in net_groups:
            if 'tags' in net_group:
                for tag in net_group['tags']:
                    if tag == checked_tag or (
                            type(tag) is dict and checked_tag in tag):
                        all_net_groups_with_tag.add(net_group['name'])
                        break
        return all_net_groups_with_tag

    @property
    def instructions(self):
        return self._instructions

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, is_valid):
        self._valid = is_valid

    def get_dependencies(self):
        return ['network-groups-2.0']
