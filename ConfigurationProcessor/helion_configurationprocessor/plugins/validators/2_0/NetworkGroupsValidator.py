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


LOG = logging.getLogger(__name__)


class NetworkGroupsValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(NetworkGroupsValidator, self).__init__(
            2.0, instructions, config_files,
            'network-groups-2.0')
        self._valid = False
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())

        version = float(self.version())

        input = self._create_content(version, "network-groups")
        self._valid = self.validate_schema(input, "network_group")
        if self._valid:
            network_groups = input['network-groups']
            self._validate_names(network_groups)
            self._validate_lb_roles(network_groups)
            self._validate_lb_external_name(network_groups)
            self._validate_provider_physnet_given(network_groups)
            self._validate_provider_physnet_same_in_netgroup(network_groups)
            self._validate_physnet_unique_among_netgroups(network_groups)
            self._validate_vlan_ranges_in_tags(network_groups)
            self._validate_vxlan_ranges_in_tags(network_groups)
        LOG.info('%s()' % KenLog.fcn())
        return self._valid

    def _validate_names(self, network_groups):
        names = set()
        for group in network_groups:
            if group['name'] in names:
                msg = ("Network Group %s is defined more than once." %
                       (group['name']))
                self.add_error(msg)
                self._valid = False
            else:
                names.add(group['name'])

    def _validate_lb_roles(self, network_groups):
        internal_found = False
        for group in network_groups:
            for lb in group.get('load-balancers', []):
                if len(lb.get('roles', [])) == 0:
                    msg = ("%s:%s: Load balancer has no roles defined" %
                           (group['name'], lb['name']))
                    self.add_error(msg)
                    continue

                for role in lb['roles']:
                    if role == 'public':
                        if len(lb['roles']) > 1:
                            msg = ("%s:%s: Load balancer role 'public' can not be combined "
                                   "with any other role. " %
                                   (group['name'], lb['name']))
                            self.add_error(msg)
                    elif role in ['internal', 'default']:
                        internal_found = True

        if not internal_found:
            msg = ("No load balancer defined for role 'internal' or 'default'")
            self.add_error(msg)

    def _validate_lb_external_name(self, network_groups):
        for group in network_groups:
            for lb in group.get('load-balancers', []):
                if 'external-name' in lb and lb['external-name'] is None:
                    msg = ("%s:%s: Load balancer external-name is blank.\n"
                           "  Either comment out this line to generate URLs that include IP addresses\n"
                           "  or provide a name that can be resolved in your network." %
                           (group['name'], lb['name']))
                    self.add_error(msg)

    def _validate_provider_physnet_given(self, network_groups):
        net_vlan_tag = 'neutron.networks.vlan'
        net_flat_tag = 'neutron.networks.flat'
        provider_net_attr = 'provider-physical-network'
        self._validate_tag_has_attribute_value(net_vlan_tag,
                                               provider_net_attr,
                                               network_groups)
        self._validate_tag_has_attribute_value(net_flat_tag,
                                               provider_net_attr,
                                               network_groups)

    def _validate_tag_has_attribute_value(self, net_tag, attr, network_groups):
        """
        Given a network tag with a required attribute, make sure that all
        instances of the tag have the required attribute with an actual value.

        :param net_tag: name of a network tag which has a required attribute
        :param attr: the required attribute of net_tag
        :param network_groups: list of network groups
        """
        for net_group in self._get_network_groups_with_tags(network_groups):
            for tag in net_group['tags']:
                tag_dict = tag if type(tag) is dict and net_tag in tag else None
                if tag == net_tag or tag_dict and (
                        not tag_dict[net_tag] or
                        tag_dict[net_tag] == attr or
                        attr not in tag_dict[net_tag] or
                        not tag_dict[net_tag][attr]):
                    msg = ("Network group %s has the tag '%s', but '%s' is "
                           "missing the required attribute '%s'. Please "
                           "provide the required '%s' and its value." %
                           (net_group['name'], net_tag, net_tag,
                            attr, attr))
                    self.add_error(msg)
                    self._valid = False

    def _validate_provider_physnet_same_in_netgroup(self, network_groups):
        """
        Makes sure that network groups which have multiple instances of
        'provider-physical-network' provide the same value for each instance
        of 'provider-physical-network' (i.e. 'flatnet1' for
        'neutron.networks.flat' and 'physnet1' for 'neutron.networks.vlan' in
        the same network group is invalid).

        :param network_groups: list of network groups
        """
        net_groups_to_physnets = self._get_physnets_per_netgroup(network_groups)
        for net_group, physnets in net_groups_to_physnets.items():
            first_physnet = ''
            for physnet in physnets:
                if not first_physnet:
                    first_physnet = physnet
                elif physnet != first_physnet:
                    msg = ("Network group %s has tags with multiple different "
                           "values for 'provider-physical-network'. All "
                           "values of 'provider-physical-network' must be the "
                           "same within a network group." % net_group)
                    self.add_error(msg)
                    self._valid = False
                    break

    def _validate_physnet_unique_among_netgroups(self, network_groups):
        """
        Makes sure that each network group's 'provider-physical-network' is
        unique with respect to all other network groups.

        :param network_groups: list of network groups
        """
        all_physnets_set = set()
        net_groups_to_physnets = self._get_physnets_per_netgroup(network_groups)
        for net_group, physnets in net_groups_to_physnets.items():
            for physnet in physnets:
                if physnet not in all_physnets_set:
                    all_physnets_set.add(physnet)
                else:
                    msg = ("Network group %s: provider-physical-network '%s' "
                           "is being used by another network group. Values "
                           "for 'provider-physical-network' cannot be shared "
                           "across network groups." % (net_group, physnet))
                    self.add_error(msg)
                    self._valid = False
                break

    def _get_physnets_per_netgroup(self, network_groups):
        """
        :param network_groups: list of network groups
        :return: a dict which maps a network_group name to a list of
        'provider-physical-network' values given in that network group.

        Example: {'MGMT': ['physnet1', 'flatnet1'],
                  'GUEST': ['guestnet1']}
        """
        physnet_key = 'provider-physical-network'
        net_group_to_physnets = {}
        for net_group in self._get_network_groups_with_tags(network_groups):
            net_group_to_physnets[net_group['name']] = []
            for dict_tag in self._get_dict_tags_from_network_group(net_group):
                vlan_tag = dict_tag.get('neutron.networks.vlan', '')
                flat_tag = dict_tag.get('neutron.networks.flat', '')
                for tag in [tag for tag in (vlan_tag, flat_tag) if tag]:
                    if physnet_key in tag and tag[physnet_key]:
                        net_group_to_physnets[net_group['name']].append(tag[physnet_key])
        return net_group_to_physnets

    def _validate_vlan_ranges_in_tags(self, network_groups):
        vlan_min, vlan_max = (1, 4094)

        for net_group in self._get_network_groups_with_tags(network_groups):
            for tag in self._get_dict_tags_from_network_group(net_group):
                vlan_tag = tag.get('neutron.networks.vlan', '')
                if vlan_tag and 'tenant-vlan-id-range' in vlan_tag:
                    start, end = vlan_tag['tenant-vlan-id-range'].split(':')
                    start, end = int(start), int(end)
                    if not (vlan_min <= start <= end <= vlan_max):
                        msg = ("Network group %s: tenant-vlan-id-range '%s' "
                               "is invalid. Please specify a range within "
                               "[%s:%s]" %
                               (net_group['name'],
                                vlan_tag['tenant-vlan-id-range'],
                                vlan_min, vlan_max))
                        self.add_error(msg)
                        self._valid = False

    def _validate_vxlan_ranges_in_tags(self, network_groups):
        vxlan_min, vxlan_max = (0, 16777215)

        for net_group in self._get_network_groups_with_tags(network_groups):
            for tag in self._get_dict_tags_from_network_group(net_group):
                vxlan_tag = tag.get('neutron.networks.vxlan', '')
                if vxlan_tag and 'tenant-vxlan-id-range' in vxlan_tag:
                    start, end = vxlan_tag['tenant-vxlan-id-range'].split(':')
                    start, end = int(start), int(end)
                    if not (vxlan_min <= start <= end <= vxlan_max):
                        msg = ("Network group %s: tenant-vxlan-id-range '%s' "
                               "is invalid. Please specify a range within "
                               "[%s:%s]" %
                               (net_group['name'],
                                vxlan_tag['tenant-vxlan-id-range'],
                                vxlan_min, vxlan_max))
                        self.add_error(msg)
                        self._valid = False

    @staticmethod
    def _get_network_groups_with_tags(network_groups):
        return (group for group in network_groups if 'tags' in group)

    @staticmethod
    def _get_dict_tags_from_network_group(network_group):
        return (tag for tag in network_group['tags'] if type(tag) is dict)

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
        return []
