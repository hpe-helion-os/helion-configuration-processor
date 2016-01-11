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


class ServerGroup(object):

    #
    # Get the name of a Server Group
    #
    @staticmethod
    def name(elem_sg):
        return elem_sg.get('name', None)

    #
    # Get all Server Groups in a Server Group
    #
    @staticmethod
    def server_groups(elem_sg):
        return elem_sg.get('server-groups', [])

    #
    # Add a Server Group object to a Server Group, and set
    # up a parent value in the child
    #
    @staticmethod
    def add_group(elem_sg, group):
        if 'groups' not in elem_sg:
            elem_sg['groups'] = []
        elem_sg['groups'].append(group)
        group['parent'] = elem_sg

    #
    # Remove the parent element.  We need to do this
    # before saving the internal model, as yaml can't cope
    # with loops
    #
    @staticmethod
    def clear_parent(elem_sg):
        if 'parent' in elem_sg:
            del (elem_sg['parent'])

    #
    # Add a server object to a Server Group
    #
    @staticmethod
    def add_server(elem_sg, server):
        if 'servers' not in elem_sg:
            elem_sg['servers'] = []
        elem_sg['servers'].append(server)

    #
    # Find an available server in a list of server groups
    #
    @staticmethod
    def get_server(sg_list, state, roles, default=None, child=False):

        res = None
        for sg in sg_list:
            for server in sg.get('servers', []):
                if server['state'] == state and server['role'] in roles:
                    res = server
                    break

            # Try any sub groups
            if not res:
                res, subgroup = ServerGroup.get_server(sg.get('groups', []),
                                                       state,
                                                       roles)

            # Always set the failure zone of the server and return the name
            # of the top group we took the resource from
            if res:
                zone = sg.get('name', None)
                return res, zone

        # None found - try the default
        if default:
            return ServerGroup.get_server([default], state, roles, None)
        else:
            return None, None

    #
    # Find a specific server in a list of server groups
    #
    @staticmethod
    def get_zone(sg_list, server_id, default=None, child=False):

        res = None
        for sg in sg_list:
            for server in sg.get('servers', []):
                if server['id'] == server_id:
                    res = server
                    break

            # Try any sub groups
            if not res:
                res = ServerGroup.get_zone(sg.get('groups', []),
                                           server_id)

            # Always return the group in the seach list, even if the
            # server is in a sub group
            if res:
                zone = sg.get('name', None)
                return zone

        # None found - try the default
        if default:
            return ServerGroup.get_zone([default], server_id, None)
        else:
            return None

    #
    # Get the list of networks in a Server Group
    #
    @staticmethod
    def networks(elem_sg):
        return elem_sg.get('networks', [])

    #
    # Add a network object to a Server Group
    #
    @staticmethod
    def add_network(elem_sg, network, net_group):
        if 'network-groups' not in elem_sg:
            elem_sg['network-groups'] = {}
        elem_sg['network-groups'][net_group] = network

    #
    # Find a network in a particular network group
    # by walking up the tree from a server group
    #
    @staticmethod
    def find_network(elem_sg, net_group, default=None):

        res = None
        if elem_sg:
            if net_group in elem_sg.get('network-groups', {}):
                res = elem_sg['network-groups'][net_group]
            elif 'parent' in elem_sg:
                res = ServerGroup.find_network(elem_sg['parent'], net_group)

            if res:
                return res

        # None found - try the default
        if default:
            return ServerGroup.find_network(default, net_group)
        else:
            return None
