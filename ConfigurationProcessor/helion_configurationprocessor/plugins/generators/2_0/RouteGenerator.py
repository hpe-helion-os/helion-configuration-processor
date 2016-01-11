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

from helion_configurationprocessor.cp.model.CPLogging import \
    CPLogging as KenLog
from helion_configurationprocessor.cp.model.GeneratorPlugin \
    import GeneratorPlugin
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel


LOG = logging.getLogger(__name__)


class RouteGenerator(GeneratorPlugin):
    def __init__(self, instructions, models, controllers):
        super(RouteGenerator, self).__init__(
            2.0, instructions, models, controllers,
            'route-generator-2.0')
        LOG.info('%s()' % KenLog.fcn())

    def generate(self):
        LOG.info('%s()' % KenLog.fcn())

        self._action = KenLog.fcn()
        cloud_internal = CloudModel.internal(self._models['CloudModel'])

        control_planes = CloudModel.get(cloud_internal, 'control-planes', {})
        # If we have an error in an earlier generator we may not have
        # control_planes in the internal model
        if not control_planes:
            return

        routes = {}
        for cp_name, cp in control_planes.iteritems():

            load_balancers = cp.get('load-balancers', {})

            for cluster in cp['clusters']:
                for server in cluster.get('servers', []):
                    self._add_routes_from_server(cp, server, load_balancers, routes)

            for r_name, r in cp.get('resources', {}).iteritems():
                for server in r.get('servers', []):
                    self._add_routes_from_server(cp, server, load_balancers, routes)

        #
        default_routes = {}
        # Warn about any routes using the "default" route
        for src_net, net_routes in routes.iteritems():
            for dest_net, route_data in net_routes.iteritems():
                if route_data['default']:
                    hosts = set()
                    if src_net not in default_routes:
                        default_routes[src_net] = []
                    for src, src_data in route_data['used_by'].iteritems():
                        for dest, host_list in src_data.iteritems():
                            for host in host_list:
                                hosts.add(host)
                    default_routes[src_net].append({'net': dest_net, 'hosts': hosts})

        if default_routes:
            msg = ("Default routing used between networks\n"
                   "The following networks are using a 'default' route rule. To remove this warning\n"
                   "either add an explict route in the source network group or force the network to\n"
                   "attach in the interface model used by the servers.\n")
            for src in sorted(default_routes):
                dest_list = default_routes[src]
                for dest_data in dest_list:
                    msg += "  %s to %s\n" % (src, dest_data['net'])
                    for host in sorted(dest_data['hosts']):
                        msg += "    %s\n" % (host)
            self.add_warning(msg)

        CloudModel.put(cloud_internal, 'routes', routes)

    #
    # Add the set of routes used by components on a server
    #
    def _add_routes_from_server(self, cp, server, load_balancers, routes):

        server_routes = {}

        # Build a list of the networks we can route to
        available_routes = {}
        for iface, iface_data in server.get('interfaces', {}).iteritems():
            for net_name, net_data in iface_data.get('networks', {}).iteritems():

                available_routes[net_name] = net_name
                server_routes[net_name] = {}

                for route in net_data.get('routes', []):
                    if route['default']:
                        name = 'default'
                    else:
                        name = route['net_name']
                    available_routes[name] = net_name

        for comp_name in server['components']:
            for relationship, consumes in cp['components'][comp_name]['consumes'].iteritems():
                consumes_name = consumes['name']

                num_vips = len(consumes.get('vips', {}))
                num_members = len(consumes.get('members', {}))
                if num_vips + num_members == 0:
                    continue

                num_routes = 0
                required_nets = {}

                for role, vip_data in consumes.get('vips', {}).iteritems():

                    # 'public' entires are just for backwards compatibility in some
                    # playbooks
                    if role in ['public']:
                        continue

                    for vip in vip_data:
                        to_network = vip['network']

                        # Keep track of all of the routes for this consumes for the error
                        # message if we don't find any
                        if to_network not in required_nets:
                            required_nets[to_network] = set()
                        required_nets[to_network].add(vip['host'])

                        found = self._add_route_from_server(server,
                                                            to_network=to_network,
                                                            src=comp_name,
                                                            dest=consumes_name,
                                                            available_routes=available_routes,
                                                            server_routes=server_routes)
                        if found:
                            num_routes += 1
                        else:
                            msg = ("Server %s (id: %s) has no route to network %s "
                                   "needed for '%s' to connect to '%s'" %
                                   (server['name'], server['id'], to_network,
                                    comp_name, consumes_name))
                            self.add_warning(msg)

                for role, hosts in consumes.get('members', {}).iteritems():

                    # 'public' entires are just for backwards compatibility in some
                    # playbooks
                    if role in ['public']:
                        continue

                    failed_members = []
                    for host in hosts:
                        to_network = host['network']

                        # Keep track of all of the routes for this consumes for the error
                        # message if we don't find any
                        if to_network not in required_nets:
                            required_nets[to_network] = set()
                        required_nets[to_network].add(host['host'])

                        found = self._add_route_from_server(server,
                                                            to_network=to_network,
                                                            src=comp_name,
                                                            dest=consumes_name,
                                                            available_routes=available_routes,
                                                            server_routes=server_routes)
                        if not found:
                            failed_members.append((host['host'], host['network']))

                    # Where we have a list of members we need a route to all hosts
                    if len(failed_members) > 0:
                        msg = ("Server %s (id: %s) has no route to network(s) required' "
                               "to enable '%s' to connect to '%s'.\n" %
                               (server['name'], server['id'], comp_name, consumes_name))
                        for host, host_net in failed_members:
                            msg += "    %s (%s)\n" % (host_net, host)
                            self.add_warning(msg)
                    else:
                        num_routes += 1

                # If there are no routes to any vip of set of members for this consumes
                # treat that as an error
                if num_routes == 0:
                    msg = ("Server %s (id: %s) has no route to network(s) required' "
                           "to enable '%s' to connect to '%s'.\n" %
                           (server['name'], server['id'], comp_name, consumes_name))
                    for network, hosts in required_nets.iteritems():
                        msg += "    %s, %s)\n" % (network, str(hosts))
                    self.add_error(msg)

            # Check any routes required for load balancers on this server
            for lb, lb_data in load_balancers.iteritems():
                if lb not in server['components']:
                    continue

                for vip, vip_data in lb_data.iteritems():
                    failed_hosts = []
                    for host in vip_data['hosts']:
                        found = self._add_route_from_server(server,
                                                            to_network=host['network'],
                                                            src=lb,
                                                            dest=vip,
                                                            available_routes=available_routes,
                                                            server_routes=server_routes)
                        if not found:
                            failed_hosts.append((host['hostname'], host['network']))

                    if len(failed_hosts) > 0:
                        msg = ("Server %s (id: %s) has no route to network(s) required' "
                               "to enable '%s' to connect to '%s'.\n" %
                               (server['name'], server['id'], lb, vip))
                        for host, host_net in failed_hosts:
                            msg += "    %s (%s)\n" % (host_net, host)
                        self.add_error(msg)

        server['routes'] = server_routes

        # Add to the list of routes in the cloud
        for server_net, net_routes in server_routes.iteritems():
            for target_net, route_data in net_routes.iteritems():

                # Create the entries if we don't have them
                if server_net not in routes:
                    routes[server_net] = {}
                if target_net not in routes[server_net]:
                    routes[server_net][target_net] = {'default': route_data['default'],
                                                      'used_by': {}}

                for src, dest in route_data['used_by']:
                    if src not in routes[server_net][target_net]['used_by']:
                        routes[server_net][target_net]['used_by'][src] = {}
                    if dest not in routes[server_net][target_net]['used_by'][src]:
                        routes[server_net][target_net]['used_by'][src][dest] = []

                    routes[server_net][target_net]['used_by'][src][dest].append(server['name'])

    #
    # Find which network component 'src' will use to connect to 'dest' which is on
    # network 'to_network', and add that route the list for a server
    #
    def _add_route_from_server(self, server, to_network, src, dest, available_routes, server_routes):

        if to_network in available_routes:
            server_network = available_routes[to_network]
            default = False
        elif 'default' in available_routes:
            server_network = available_routes['default']
            default = True
        else:
            return False

        # No route needed for the same network
        if server_network == to_network:
            return True

        network_routes = server_routes[server_network]
        if to_network not in network_routes:
            network_routes[to_network] = {'used_by': set(),
                                          'default': default}

        network_routes[to_network]['used_by'].add((src, dest))
        return True

    def get_dependencies(self):
        return ['cloud-cplite-2.0',
                'consumes-generator-2.0']
