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


class CrossReferenceValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(CrossReferenceValidator, self).__init__(
            2.0, instructions, config_files,
            'cross-reference-2.0')
        self._valid = True
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())
        version = float(self.version())

        #
        # Validate references between objects.
        #

        # Check each zone in a list is a server group
        def _validate_zones(zones, server_groups, context):
            for zone in zones:
                if zone not in server_groups:
                    msg = ("Failure zone %s referenced in %s "
                           "is not defined as a server group" %
                           (zone, context))
                    self.add_error(msg)
                    self._valid = False

        # Check each role in a list exists
        def _validate_roles(roles, server_roles, context):
            if isinstance(roles, basestring):
                roles = [roles]
            else:
                roles = roles
            for role in roles:
                if role not in server_roles:
                    msg = ("Server role %s referenced in %s "
                           "is not defined" %
                           (role, context))
                    self.add_error(msg)
                    self._valid = False

        control_planes = self._get_dict_from_config_value(version, 'control-planes')
        server_roles = self._get_dict_from_config_value(version, 'server-roles')
        disk_models = self._get_dict_from_config_value(version, 'disk-models')
        iface_models = self._get_dict_from_config_value(version, 'interface-models')
        network_groups = self._get_dict_from_config_value(version, 'network-groups')
        networks = self._get_dict_from_config_value(version, 'networks')
        pass_through = self._get_config_value(version, 'pass-through')
        server_groups = self._get_dict_from_config_value(version, 'server-groups')
        bm_servers = self._get_config_value(version, 'servers')
        firewall_rules = self._get_config_value(version, 'firewall-rules')

        if not firewall_rules:
            firewall_rules = []

        # Check server roles and failure zones control planes
        for cp_name, cp in control_planes.iteritems():

            _validate_zones(cp.get('failure-zones', []), server_groups,
                            context=cp['name'])

            for cluster in cp['clusters']:
                context = "%s:%s" % (cp['name'], cluster['name'])

                _validate_roles(cluster['server-role'], server_roles, context)

                _validate_zones(cluster.get('failure-zones', []),
                                server_groups, context)

            # Have to cope with the old name in here, as validator
            # runs before the migrator
            if 'resource-nodes' in cp:
                resources = cp['resource-nodes']
            else:
                resources = cp.get('resources', [])

            for r in resources:

                _validate_roles(r['server-role'], server_roles, context)

                _validate_zones(r.get('failure-zones', []),
                                server_groups, context)

        # Check disk models in server roles
        for name, role_data in server_roles.iteritems():

            # Note: Interface model checked in server validator

            if role_data['disk-model'] not in disk_models:
                msg = ("Disk model %s referenced in %s "
                       "is not defined" %
                       (role_data['disk-model'], name))
                self.add_error(msg)
                self._valid = False

        # Check interface models are valid
        iface_net_groups = set()
        for name, data in iface_models.iteritems():
            for iface in data['network-interfaces']:
                for netgrp in iface.get('network-groups', []):
                    if netgrp in network_groups:
                        iface_net_groups.add(netgrp)
                    else:
                        msg = ("Network group %s used by interface %s in "
                               "interface model %s is not defined" %
                               (netgrp, iface['name'], name))
                        self.add_error(msg)
                        self._valid = False
                for netgrp in iface.get('forced-network-groups', []):
                    if netgrp in network_groups:
                        iface_net_groups.add(netgrp)
                    else:
                        msg = ("Network group %s used by interface %s in "
                               "interface model %s is not defined" %
                               (netgrp, iface['name'], name))
                        self.add_error(msg)
                        self._valid = False

        # Check all networks have a valid network group
        # and add them into their respective groups
        for netgrp, data in network_groups.iteritems():
            data['networks'] = []

        for net_name, net in networks.iteritems():
            if net['network-group'] not in network_groups:
                msg = ("Network group %s referenced by network %s "
                       "is not defined" % (net['network-group'], net_name))
                self.add_error(msg)
                self._valid = False
            else:
                network_groups[net['network-group']]['networks'].append(net)

        # Check all network groups routes are to another group
        net_group_routes = set()
        for netgrp, data in network_groups.iteritems():
            for route in data.get('routes', []):
                if route != 'default' and route not in network_groups:
                    msg = ("Network group %s route %s is not a valid network group."
                           % (netgrp, route))
                    self.add_error(msg)
                    self._valid = False
                elif route == netgrp:
                    msg = ("Network group %s does not need a route to itself."
                           % (netgrp))
                    self.add_warning(msg)
                else:
                    net_group_routes.add(route)

        # Check all network groups are associated with at least one iface model
        # or used as a route
        for netgrp, data in network_groups.iteritems():
            if netgrp not in iface_net_groups:
                if 'load-balancers' in data:
                    msg = ("Network group %s contains a load balancer and is not "
                           "associated with any interface model." % (netgrp))
                    self.add_error(msg)
                elif netgrp not in net_group_routes:
                    msg = ("Network group %s is not associated with any interface "
                           "model or used as a route target of a network group"
                           % (netgrp))
                    self.add_warning(msg)

        # Check all network groups have at least one network
        for netgrp, data in network_groups.iteritems():
            if (len(data['networks']) == 0
                and ('load-balancers' in data
                     or 'component-endpoints' in data
                     or 'tls-component-endpoints' in data
                     or 'service-endpoints' in data
                     or 'tls-service-endpoints' in data)):
                msg = ("Network group %s does not have any networks"
                       % (netgrp))
                self.add_error(msg)
                self._valid = False

        # Check pass through data references a valid server
        if pass_through:
            server_ids = set()
            for s in bm_servers:
                server_ids.add(s['id'])
            for pt in pass_through:
                for server_data in pt.get('servers', []):
                    if server_data['id'] not in server_ids:
                        msg = ("Invalid Server id %s with passthrough data:  %s"
                               % (server_data['id'], server_data['data']))
                        self.add_error(msg)
                        self._valid = False

        # Check that, if server_groups is defined, every server is in a group
        if server_groups:
            for s in bm_servers:
                if 'server-group' not in s:
                    msg = ("Server %s is not a member of a server-group"
                           % s['id'])
                    self.add_error(msg)
                    self._valid = False

        # Check that, if server_groups is defined, every network is in a group
            network_list = []
            for group_name, group in server_groups.iteritems():
                network_list = network_list + group.get('networks', [])
            for net_name, net in networks.iteritems():
                if net_name not in network_list:
                    msg = ("Network %s is not included in a server-group"
                           % net_name)
                    self.add_error(msg)
                    self._valid = False

        # Validate Server Groups
        child_groups = set()
        for group_name, group in server_groups.iteritems():
            for child in group.get('server-groups', []):
                if child in server_groups:
                    if child not in child_groups:
                        child_groups.add(child)
                    else:
                        msg = ("Server group %s is included in more than one "
                               "server group." % (child))
                        self.add_error(msg)
                        self._valid = False
                else:
                    msg = ("Server group %s referenced by server group %s "
                           "is not defined" % (child, group_name))
                    self.add_error(msg)
                    self._valid = False

            net_groups = set()
            for net in group.get('networks', []):
                if net in networks:
                    net_group = networks[net]['network-group']
                    if net_group in net_groups:
                        msg = ("Server group %s includes more than one "
                               "network from network group %s." %
                               (group_name, net_group))
                        self.add_error(msg)
                        self._valid = False
                    else:
                        net_groups.add(net_group)
                else:
                    msg = ("Network %s referenced by server group %s "
                           "is not defined" % (net, group_name))
                    self.add_error(msg)
                    self._valid = False

        # Check network group names in firewall rules are valid
        for rule_set in firewall_rules:
            rule_groups = rule_set.get('network-groups', [])
            if not rule_groups:
                msg = ("Firewall rule set %s: Must specify at least one "
                       "network group" % (rule_set['name']))
                self.add_error(msg)
                self._valid = False
            for net_group_name in rule_groups:
                if net_group_name != "all" and net_group_name not in network_groups:
                    msg = ("Invalid network group name %s in firewall rule set %s." %
                           (net_group_name, rule_set['name']))
                    self.add_error(msg)
                    self._valid = False

        self._check_no_orphaned_servers(server_groups, bm_servers, control_planes)

        return self._valid

    def _check_no_orphaned_servers(self, server_groups, servers, control_planes):

        # Check that all servers are in a group that can be reached from at least
        # one control plane
        groups = {}

        # Show that a set of servers with a particular role in a group or
        # any of its child groups can be used.
        def _touch(group, roles):
            if isinstance(roles, basestring):
                role_list = [roles]
            else:
                role_list = roles

            for role in group['server-roles']:
                if role in role_list:
                    group['server-roles'][role] = []

            for child in group['children']:
                if child in groups:
                    _touch(groups[child], roles)

        # Build a list of all groups
        for group_name in server_groups:
            groups[group_name] = {'children': [],
                                  'server-roles': {}}
        groups['default'] = {'children': [],
                             'server-roles': {}}

        # Add child groups to parents
        for group_name, group in server_groups.iteritems():
            for child in group.get('server-groups', []):
                groups[group['name']]['children'].append(child)

        # List servers by role within the groups
        for s in servers:
            group = s.get('server-group', 'default')
            if group not in groups:
                # This will get picked up by the server validator,
                # so just ignore it
                continue

            role = s['role']
            if role not in groups[group]['server-roles']:
                groups[group]['server-roles'][role] = []
            groups[group]['server-roles'][role].append(s['id'])

        # For each clutser and resource group find all the servers
        # we might be able to allocate - and remove them from the groups
        for cp_name, cp in control_planes.iteritems():
            for cluster in cp.get('clusters', []):
                zones = cluster.get('failure-zones', cp.get('failure-zones', ['default']))
                for zone in zones:
                    _touch(groups[zone], cluster['server-role'])

            # Have to cope with the old name in here, as validator
            # runs before the migrator
            if 'resource-nodes' in cp:
                resources = cp['resource-nodes']
            else:
                resources = cp.get('resources', [])

            for r in resources:
                zones = r.get('failure-zones', cp.get('failure-zones', ['default']))
                for zone in zones:
                    _touch(groups[zone], r['server-role'])

        # Any servers left in a group are ones we can't reach
        for group_name, group in groups.iteritems():
            for role, servers in group['server-roles'].iteritems():
                for server_id in servers:
                    if group_name == 'default':
                        msg = ("Server %s with role %s "
                               "is not in scope for selection in any cluster "
                               "or resource group" % (server_id, role))
                    else:
                        msg = ("Server %s with role %s in server group %s "
                               "is not in scope for selection in any cluster "
                               "or resource group" % (server_id, role, group_name))
                    self.add_warning(msg)

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
                'firewall-rules-2.0']
