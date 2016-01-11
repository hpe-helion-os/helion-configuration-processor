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
import six
import logging
import logging.config

from helion_configurationprocessor.cp.model.v2_0.HlmPaths \
    import HlmPaths
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel
from helion_configurationprocessor.cp.model.v2_0.ControlPlane \
    import ControlPlane
from helion_configurationprocessor.cp.model.v2_0.Cluster \
    import Cluster
from helion_configurationprocessor.cp.model.v2_0.Server \
    import Server
from helion_configurationprocessor.cp.model.v2_0.ResourceNode \
    import ResourceNode
from helion_configurationprocessor.cp.model.v2_0.Interface \
    import Interface
from helion_configurationprocessor.cp.model.v2_0.Network \
    import Network

from helion_configurationprocessor.cp.model.BuilderPlugin \
    import BuilderPlugin
from helion_configurationprocessor.cp.model.BuilderPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog

from helion_configurationprocessor.plugins.builders.Diagram.Box \
    import Box


LOG = logging.getLogger(__name__)


class DiagramBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(DiagramBuilder, self).__init__(
            2.0, instructions, models, controllers,
            'diagram-2.0')
        LOG.info('%s()' % KenLog.fcn())

        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions,
                                                   self.cloud_desc)
        self._file_path = os.path.join(self._file_path, 'info')

        self._cloud_model = self._models['CloudModel']
        self._cloud_version = CloudModel.version(self._cloud_model,
                                                 self._version)
        self._cloud_internal = CloudModel.internal(self._cloud_model)

        HlmPaths.make_path(self._file_path)

        self._padding_x = 2
        self._padding_y = 2
        self._server_width = 50
        self._line_width = 136

    def build(self):
        LOG.info('%s()' % KenLog.fcn())

        file_name = '%s/CloudDiagram.txt' % self._file_path
        self.add_artifact(file_name, ArtifactMode.CREATED)
        fp = open(file_name, 'w')

        self._render_control_planes(fp)

        fp.close()

    def _determine_size_for_control_plane(self, elem_r):
        LOG.info('%s()' % KenLog.fcn())

        width = 0
        height = self._padding_y

        clusters = ControlPlane.clusters(elem_r)

        for elem_c in clusters:
            (t_w, t_h) = self._determine_size_for_cluster(elem_r, elem_c)

            if t_w > width:
                width = t_w

            height += t_h + 1

        width += (self._padding_x * 2)
        height += 1

        res_height = self._determine_height_for_resource_nodes(elem_r)
        height += res_height

        return width, height

    def _determine_size_for_cluster(self, elem_r, elem_c):
        LOG.info('%s()' % KenLog.fcn())

        width = 0
        height = 0

        for elem_s in Cluster.servers(elem_c):
            (m_w, m_h) = self._determine_size_for_server(
                elem_r, elem_c, elem_s)

            width += (m_w + (self._padding_x * 2))
            height = (m_h + (self._padding_y * 2))

        return width, height

    def _determine_size_for_server(self, elem_r, elem_c, elem_s):
        LOG.info('%s()' % KenLog.fcn())

        num_components = Server.num_components(elem_s)
        num_services = Server.num_services(elem_s)

        width = self._server_width - self._padding_x

        height = self._padding_y
        height += num_services
        height += num_components
        height += 3  # Separation

        routes = Server.routes(elem_s)
        for i, elem_i in six.iteritems(Server.interfaces(elem_s)):
            height += 1
            for n, elem_n in six.iteritems(Interface.networks(elem_i)):
                height += 1
                for r in routes.get(n, []):
                    height += 1

        height += self._padding_y

        return width, height

    def _determine_height_for_resource_nodes(self, elem_r):
        LOG.info('%s()' % KenLog.fcn())

        height = 0

        for elem_rn in ControlPlane.resources(elem_r):
            height_s = 0
            for elem_s in ResourceNode.servers(elem_rn):
                h = self._determine_height_for_resource_node(
                    elem_r, elem_rn, elem_s)
                if h > height_s:
                    height_s = h

            height += height_s
            height += 1
            height += self._padding_y
            height += 1

        return height

    def _determine_height_for_resource_node(self, elem_r, elem_rn, elem_s):
        LOG.info('%s()' % KenLog.fcn())

        height = self._padding_y
        height += Server.num_services(elem_s)
        height += Server.num_components(elem_s)
        height += 3  # Separation

        routes = Server.routes(elem_s)
        for i, elem_i in six.iteritems(Server.interfaces(elem_s)):
            height += 1
            for n, elem_n in six.iteritems(Interface.networks(elem_i)):
                height += 1
                for r in routes.get(n, []):
                    height += 1

        height += self._padding_y
        return height

    def _render_control_planes(self, fp):
        LOG.info('%s()' % KenLog.fcn())

        control_planes = CloudModel.get(self._cloud_version, 'control-planes')
        for elem_r in control_planes:
            (r_w, r_h) = self._determine_size_for_control_plane(elem_r)
            r_box = Box(r_w, r_h)

            r_type = ControlPlane.name(elem_r)
            r_type_name = ControlPlane.region_name(elem_r)

            title = 'ControlPlane: %s (%s)' % (r_type_name, r_type)
            r_box.set_title(title)

            tier_y = 2
            tot_box_w = 0
            for elem_c in ControlPlane.clusters(elem_r):
                (t_w, t_h) = self._determine_size_for_cluster(
                    elem_r, elem_c)
                t_box = Box(t_w, t_h)

                if tot_box_w == 0:
                    tot_box_w = t_w

                title = 'Cluster %s (%s)' % (
                    Cluster.name(elem_c), Cluster.id(elem_c))

                t_box.set_title(title)
                r_box.add_layer(t_box, 2, tier_y)

                tier_y += t_h + (self._padding_y / 2)

                member_x = 2
                for elem_s in Cluster.servers(elem_c):
                    (m_w, m_h) = self._determine_size_for_server(
                        elem_r, elem_c, elem_s)
                    m_box = Box(m_w, m_h)

                    ip = Server.address(elem_s)
                    if ip:
                        title = '%s (%s)' % (Server.name(elem_s), ip)
                    else:
                        title = '%s' % Server.name(elem_s)

                    m_box.set_title(title)

                    t_box.add_layer(m_box, member_x, 2)
                    member_x += (self._server_width + self._padding_x)

                    service_y = 2
                    services = Server.services(elem_s)
                    for elem_c in sorted(services):
                        m_box.add_string_absolute(elem_c, 2, service_y)
                        service_y += 1
                        for elem_comp in sorted(services[elem_c]):
                            m_box.add_string_absolute(elem_comp, 4, service_y)
                            service_y += 1

                    service_y += 1
                    sep = "-" * m_w
                    m_box.add_string_absolute(sep, 2, service_y)
                    service_y += 2

                    interfaces = Server.interfaces(elem_s)
                    routes = Server.routes(elem_s)
                    for i in sorted(interfaces):
                        elem_i = interfaces[i]
                        device = elem_i['device']['name']
                        if 'bond-data' in elem_i:
                            device += " ("
                            first = True
                            for bond_dev in elem_i['bond-data'].get('devices', []):
                                if not first:
                                    device += ", "
                                first = False
                                device += "%s" % bond_dev['name']
                            device += ")"
                        m_box.add_string_absolute(device, 2, service_y)
                        service_y += 1
                        networks = Interface.networks(elem_i)
                        for n in sorted(networks):
                            elem_n = networks[n]
                            name = Network.name(elem_n)
                            if 'addr' in elem_n:
                                name += " (%s)" % elem_n['addr']
                            m_box.add_string_absolute(name, 4, service_y)
                            service_y += 1

                            net_routes = routes.get(n, {})
                            for r in sorted(net_routes):
                                elem_route = net_routes[r]
                                r_name = "-> %s " % r
                                if elem_route['default']:
                                    r_name += "(default)"
                                m_box.add_string_absolute(r_name, 6, service_y)
                                service_y += 1

            r_y = tier_y
            self._render_resource_nodes(r_box, r_y, elem_r, tot_box_w)

            r_box.display(fp)

    def _render_resource_nodes(self, r_box, r_y, elem_r, w):
        LOG.info('%s()' % KenLog.fcn())

        for elem_rn in ControlPlane.resources(elem_r):

            # Build a list of server types by AZ and role
            server_types = {}
            AZs = set()
            for elem_s in ResourceNode.servers(elem_rn):
                role = ResourceNode.server_role(elem_s)
                if role not in server_types:
                    rn_h = self._determine_height_for_resource_node(
                        elem_r, elem_rn, elem_s)
                    server_types[role] = {'height': rn_h,
                                          'zones': {}}
                AZ = ResourceNode.failure_zone(elem_s)
                AZs.add(AZ)
                if AZ not in server_types[role]['zones']:
                    server_types[role]['zones'][AZ] = {'server': elem_s,
                                                       'count': 1}
                else:
                    server_types[role]['zones'][AZ]['count'] += 1

            # Work out how height we're going to be
            res_h = 1
            for role, data in server_types.iteritems():
                res_h += data['height'] + self._padding_y
            res_w = len(AZs) * (self._server_width + self._padding_x)

            res_box = Box(res_w, res_h)
            res_box.set_title(ResourceNode.name(elem_rn))
            r_box.add_layer(res_box, 2, r_y)
            r_y += res_h + 1

            res_x = 2
            res_y = 2
            for roles, data in server_types.iteritems():
                for AZ in sorted(data['zones']):
                    elem_s = data['zones'][AZ]['server']
                    w = self._server_width - self._padding_x
                    rn_h = self._determine_height_for_resource_node(
                        elem_r, elem_rn, elem_s)
                    rn_box = Box(w, rn_h)

                    res_box.add_layer(rn_box, res_x, res_y)
                    res_x += (self._server_width + self._padding_x)

                    name = ResourceNode.name(elem_rn)

                    title = '%s (%s) (%s servers)' % (role, AZ, data['zones'][AZ]['count'])
                    rn_box.set_title(title)

                    service_y = 2
                    services = Server.services(elem_s)
                    for elem_c in sorted(services):
                        rn_box.add_string_absolute(elem_c, 2, service_y)
                        service_y += 1
                        for elem_comp in sorted(services[elem_c]):
                            rn_box.add_string_absolute(elem_comp, 4, service_y)
                            service_y += 1

                    service_y += 1
                    sep = "-" * w
                    rn_box.add_string_absolute(sep, 2, service_y)
                    service_y += 2

                    interfaces = Server.interfaces(elem_s)
                    routes = Server.routes(elem_s)
                    for i in sorted(interfaces):
                        elem_i = interfaces[i]
                        device = elem_i['device']['name']
                        if 'bond-data' in elem_i:
                            device += " ("
                            first = True
                            for bond_dev in elem_i['bond-data'].get('devices', []):
                                if not first:
                                    device += ", "
                                first = False
                                device += "%s" % bond_dev['name']
                            device += ")"
                        rn_box.add_string_absolute(device, 2, service_y)
                        service_y += 1
                        networks = Interface.networks(elem_i)
                        for n in sorted(networks):
                            elem_n = networks[n]
                            name = Network.name(elem_n)
                            if 'addr' in elem_n:
                                name += " (%s)" % elem_n['cidr']
                            rn_box.add_string_absolute(name, 4, service_y)
                            service_y += 1

                            net_routes = routes.get(n, {})
                            for r in sorted(net_routes):
                                elem_route = net_routes[r]
                                r_name = "-> %s " % r
                                if elem_route['default']:
                                    r_name += "(default)"
                                rn_box.add_string_absolute(r_name, 6, service_y)
                                service_y += 1

        return r_y
