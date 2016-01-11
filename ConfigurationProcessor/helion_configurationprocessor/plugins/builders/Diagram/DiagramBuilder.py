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

from helion_configurationprocessor.cp.model.ControlPlane import ControlPlane
from helion_configurationprocessor.cp.model.Tier import Tier
from helion_configurationprocessor.cp.model.Member import Member
from helion_configurationprocessor.cp.model.ResourceNode import ResourceNode
from helion_configurationprocessor.cp.model.Hostname import Hostname

from helion_configurationprocessor.cp.model.BuilderPlugin import BuilderPlugin
from helion_configurationprocessor.cp.model.BuilderPlugin import ArtifactMode
from helion_configurationprocessor.cp.controller.NetworkConfigController \
    import NetworkConfigController
from helion_configurationprocessor.plugins.builders.Diagram.Box import Box
from helion_configurationprocessor.cp.model.CPLogging import \
    CPLogging as KenLog


LOG = logging.getLogger(__name__)


class DiagramBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(DiagramBuilder, self).__init__(
            1, instructions, models, controllers,
            'diagram')

        LOG.info('%s()' % KenLog.fcn())

        self._padding_x = 2
        self._padding_y = 2
        self._member_width = 50
        self._line_width = 136

    def build(self):
        LOG.info('%s()' % KenLog.fcn())

        cloud_config = self._controllers['CloudConfig']
        path = cloud_config.get_output_path(self._models)

        if not os.path.exists(path):
            os.makedirs(path)

        file_name = '%s/CloudDiagram.txt' % path
        self.add_artifact(file_name, ArtifactMode.CREATED)
        fp = open(file_name, 'w')

        fp.write('Cloud: %s\n\n' % self._models['CloudModel']['cloud-name'])

        self._render_control_planes(fp)

        fp.close()

    def _determine_size_for_control_plane(self, elem_cp):
        LOG.info('%s(elem_cp="%s")' % (
            KenLog.fcn(), ControlPlane.get_name(elem_cp)))

        width = 0
        height = self._padding_y

        for elem_t in elem_cp['tiers']:
            if not Tier.is_active_or_empty(elem_t):
                continue

            (t_w, t_h) = self._determine_size_for_tier(elem_cp, elem_t)

            if t_w > width:
                width = t_w

            height += t_h

        width += (self._padding_x * 2)
        height += (self._padding_y * 2)

        height += self._determine_height_for_resource_nodes(elem_cp)
        height += self._determine_height_for_cp_networks(elem_cp)

        return width, height

    def _determine_size_for_tier(self, elem_cp, elem_t):
        LOG.info('%s()' % KenLog.fcn())

        width = 0
        height = 0

        for m, elem_m in six.iteritems(elem_t['members']):
            if not Member.is_active(elem_m):
                continue

            if m.lower() == 'vip':
                continue

            (m_w, m_h) = self._determine_size_for_member(
                elem_cp, elem_t, elem_m)

            width += (m_w + (self._padding_x * 2))
            height = (m_h + (self._padding_y * 2))

        return width, height

    def _determine_size_for_member(self, elem_cp, elem_t, elem_m):
        LOG.info('%s()' % KenLog.fcn())

        num_services = len(Member.get_services(elem_m))
        num_networks = 0

        tier_networks = self._get_tier_member_networks(elem_cp, elem_t)
        if tier_networks:
            num_networks = len(tier_networks)

        width = self._member_width - self._padding_x

        height = self._padding_y
        height += num_services
        height += 1  # Dashes
        height += num_networks
        height += self._padding_y

        return width, height

    def _determine_height_for_resource_nodes(self, elem_cp):
        LOG.info('%s(elem_cp="%s")' % (
            KenLog.fcn(), ControlPlane.get_name(elem_cp)))

        height = 0

        for nt, elem_rn in six.iteritems(elem_cp['resource-nodes']):
            if not elem_rn:
                continue

            height += self._determine_height_for_resource_node(
                elem_cp, nt, elem_rn)

        if height:
            height += (self._padding_y * 2)
            height += 1  # Separation

        return height

    def _determine_height_for_resource_node(self, elem_cp, node_type, elem_rn):
        LOG.info('%s(elem_cp="%s", node_type="%s", elem_rn="%s")' % (
            KenLog.fcn(),
            ControlPlane.get_name(elem_cp),
            node_type,
            ResourceNode.get_hostname(elem_rn)))

        num_rn_allocations = 0
        allocations = self._get_resource_node_allocations(elem_cp, node_type)
        LOG.info('-------------------------------------')
        for k, v in six.iteritems(allocations):
            LOG.info(v)
            if 'start' in v and 'end' in v:
                num_rn_allocations += 1
        LOG.info('------------------------------------- %d' %
                 num_rn_allocations)

        height = self._padding_y
        height += len(ResourceNode.get_services(elem_rn))
        height += 1  # Dashes
        height += num_rn_allocations
        height += self._padding_y

        return height

    def _determine_height_for_cp_networks(self, elem_cp):
        LOG.info('%s()' % KenLog.fcn())

        height = 0

        interfaces = dict()

        nt = elem_cp['network-topology']

        for k, v in six.iteritems(nt):
            (intf, vlan_tag) = self._get_interface_info(elem_cp['type'], k)
            index = '%s-%s' % (intf, vlan_tag)

            if index not in interfaces:
                interfaces[index] = dict()
                interfaces[index]['interface'] = intf
                interfaces[index]['vlan-tag'] = vlan_tag
                interfaces[index]['mnemonics'] = []

            if k not in interfaces[index]['mnemonics']:
                interfaces[index]['mnemonics'].append(k)

        for k, v in six.iteritems(interfaces):
            height += self._determine_height_for_cp_interface(v)
            height += 1  # Separation

        return height

    def _determine_height_for_cp_interface(self, intf):
        LOG.info('%s()' % KenLog.fcn())

        height = self._padding_y
        height += len(intf['mnemonics'])
        height += self._padding_y

        return height

    def _render_control_planes(self, fp):
        LOG.info('%s()' % KenLog.fcn())

        svc_controller = self._controllers['Service']
        res_controller = self._controllers['Resource']
        es_resource = res_controller.resource('external-service')
        cloud_model = self._models['CloudModel']

        for elem_cp in self._models['CloudModel']['control-planes']:
            if not ControlPlane.is_active(elem_cp):
                continue

            (cp_w, cp_h) = self._determine_size_for_control_plane(elem_cp)
            cp_box = Box(cp_w, cp_h)

            cp_type = elem_cp['type']
            if elem_cp['type'].lower() == 'rcp':
                cp_type = '%s%s' % (elem_cp['type'], elem_cp['id'])

            cp_type_name = ControlPlane.get_name(elem_cp)

            title = '%s (%s, Region: %s)' % (
                cp_type.upper(), cp_type_name, elem_cp['region-name'])
            cp_box.set_title(title)

            tier_y = 2
            tot_box_w = 0
            for elem_t in elem_cp['tiers']:
                if not Tier.is_active_or_empty(elem_t):
                    continue

                (t_w, t_h) = self._determine_size_for_tier(elem_cp, elem_t)
                t_box = Box(t_w, t_h)

                if tot_box_w == 0:
                    tot_box_w = t_w

                title = 'T%d (Service Tier)' % int(elem_t['id'])

                t_box.set_title(title)
                cp_box.add_layer(t_box, 2, tier_y)

                tier_y += t_h + (self._padding_y / 2)

                member_x = 2
                for m, elem_m in six.iteritems(elem_t['members']):
                    if not Member.is_active(elem_m):
                        continue

                    if m.lower() == 'vip':
                        continue

                    (m_w, m_h) = self._determine_size_for_member(
                        elem_cp, elem_t, elem_m)
                    m_box = Box(m_w, m_h)

                    title = 'M%s (Member)' % m
                    m_box.set_title(title)

                    t_box.add_layer(m_box, member_x, 2)
                    member_x += (self._member_width + self._padding_x)

                    service_y = 2
                    for elem_s in Member.get_services(elem_m):
                        svc_name = svc_controller.service_output(
                            elem_s['name'])

                        if not es_resource.is_external(cloud_model, svc_name):
                            m_box.add_string_centered(svc_name, service_y)

                        else:
                            ext_string = '%s (ext)' % svc_name
                            ex, ey = m_box.get_centered_pos(
                                svc_name, service_y)

                            m_box.add_string_absolute(ext_string, ex, ey)

                        service_y += 1

                    tm_networks = self._get_tier_member_networks(elem_cp,
                                                                 elem_t)
                    if len(tm_networks) > 0:
                        m_box.add_string_centered('-------', service_y)
                        service_y += 1

                        for k, v in six.iteritems(tm_networks):
                            text = '%s - %s' % (k, v[m][-14:])
                            m_box.add_string_centered(text, service_y)
                            service_y += 1

            cp_y = tier_y
            cp_y = self._render_resource_nodes(cp_box, cp_y, elem_cp,
                                               tot_box_w)

            self._render_control_plane_networks(cp_box, cp_y, elem_cp,
                                                tot_box_w)

            cp_box.display(fp)

    def _render_resource_nodes(self, cp_box, cp_y, elem_cp, w):
        LOG.info('%s()' % KenLog.fcn())

        svc_controller = self._controllers['Service']

        for nt, elem_rn in six.iteritems(elem_cp['resource-nodes']):
            if not elem_rn:
                continue

            rn_h = self._determine_height_for_resource_node(elem_cp, nt,
                                                            elem_rn)
            rn_box = Box(w, rn_h)

            cp_box.add_layer(rn_box, 2, cp_y)
            cp_y += (rn_h + (self._padding_y / 2))

            idx_start = 'N%04d' % 1
            idx_end = 'N%04d' % elem_rn['count']

            hostname_start = '%s-%s' % (nt.upper(), idx_start)
            hostname_start = Hostname.output_format(
                self._instructions, hostname_start)

            hostname_end = '%s-%s' % (nt.upper(), idx_end)
            hostname_end = Hostname.output_format(
                self._instructions, hostname_end)

            title = '%s -> %s (Compute Node)' % (hostname_start,
                                                 hostname_end)
            rn_box.set_title(title)

            service_y = 2
            for elem_s in ResourceNode.get_services(elem_rn):
                s_name = svc_controller.service_output(elem_s)
                rn_box.add_string_centered(s_name, service_y)
                service_y += 1

            allocations = self._get_resource_node_allocations(elem_cp, nt)
            if allocations:
                rn_box.add_string_centered('-------', service_y)
                service_y += 1

                for k, v in six.iteritems(allocations):
                    if 'start' in v and 'end' in v:
                        text = '%s - %s -> %s' % (
                            k.upper(), v['start'], v['end'])
                        rn_box.add_string_centered(
                            text, service_y)
                        service_y += 1

        return cp_y

    def _render_control_plane_networks(self, cp_box, cp_y, elem_cp, w):
        LOG.info('%s()' % KenLog.fcn())

        interfaces = dict()

        for k, v in six.iteritems(elem_cp['network-topology']):
            (intf, vlan_tag) = self._get_interface_info(
                elem_cp['type'], k)
            index = '%s-%s' % (intf, vlan_tag)

            if index not in interfaces:
                interfaces[index] = dict()
                interfaces[index]['interface'] = intf
                interfaces[index]['vlan-tag'] = vlan_tag
                interfaces[index]['mnemonics'] = []

            if k not in interfaces[index]['mnemonics']:
                interfaces[index]['mnemonics'].append(k)

        for k, v in six.iteritems(interfaces):
            ni_height = self._determine_height_for_cp_interface(v)
            ni_box = Box(w, ni_height)

            cp_box.add_layer(ni_box, 2, cp_y)
            cp_y += (ni_height + (self._padding_y / 2))

            if not v['interface']:
                v['interface'] = 'unknown'

            if not v['vlan-tag']:
                v['vlan-tag'] = 'untagged'

            title = 'Network Interface %s (%s)' % (v['interface'],
                                                   v['vlan-tag'])
            ni_box.set_title(title)

            network_y = 2
            for m in v['mnemonics']:
                ni_box.add_string_centered(m.upper(), network_y)
                network_y += 1

    def _get_resource_node_allocations(self, elem_cp, node_type):
        LOG.info('%s(): node_type="%s"' % (KenLog.fcn(), node_type))

        return_value = dict()

        if len(elem_cp['resource-nodes']) == 0:
            return None

        for nt, cur_rn in six.iteritems(elem_cp['resource-nodes']):
            if not cur_rn:
                continue

            if 'allocations' not in cur_rn:
                return None

            if len(cur_rn['allocations']) == 0:
                return None

            if nt.lower() == node_type.lower():
                for allocation in cur_rn['allocations']:
                    host_enc = NetworkConfigController.decode_hostname(
                        allocation['name'])
                    mnemonic = host_enc['network-ref']

                    if mnemonic not in return_value:
                        return_value[mnemonic] = dict()

                    if host_enc['node-id'].lower() == 'n0001':
                        if 'ip-address' in allocation:
                            return_value[mnemonic]['start'] = \
                                allocation['ip-address']

                    if 'ip-address' in allocation:
                        return_value[mnemonic]['end'] = \
                            allocation['ip-address']

                break

        return return_value

    def _get_tier_member_networks(self, elem_cp, elem_t):
        LOG.info('%s()' % KenLog.fcn())

        return_value = dict()

        nt = elem_cp['network-topology']
        for k1, nv in six.iteritems(nt):
            for k2, tv in six.iteritems(nv):
                if int(k2) == int(elem_t['id']):
                    for m, elem_m in six.iteritems(elem_t['members']):
                        if not Member.is_active(elem_m):
                            continue

                        if m.lower() == 'vip':
                            continue

                        if k1 not in return_value:
                            return_value[k1] = dict()

                        return_value[k1][m] = tv[m]['ip-address']

        return return_value

    def _get_interface_info(self, cp_type, mnemonic):
        LOG.info('%s()' % KenLog.fcn())

        (intf, vlan_tag) = self._get_interface_info_for_network(
            cp_type, mnemonic)

        if not intf or not vlan_tag:
            (intf, vlan_tag) = self._get_interface_info_for_network(
                'GLOBAL', mnemonic)

        return intf, vlan_tag

    def _get_interface_info_for_network(self, cp_type, mnemonic):
        LOG.info('%s()' % KenLog.fcn())

        interface = None
        vlan_tag = None

        for elem_li in self._models['NetworkConfig']['logical-interfaces']:
            if elem_li['pool-name'].lower() == cp_type.lower():
                for elem_ln in elem_li['logical-networks']:
                    for elem_nt in elem_ln['network-traffic']:
                        if mnemonic.lower() == elem_nt['name'].lower():
                            interface = elem_li['name']
                            vlan_tag = self._get_vlan_tag(
                                interface, elem_ln['name'])
                            break

        return interface, vlan_tag

    def _get_vlan_tag(self, intf_name, seg_name):
        for elem_nt in self._models['EnvironmentConfig']['node-type']:
            for elem_im in elem_nt['interface-map']:
                if elem_im['name'].lower() == intf_name.lower():
                    for elem_lnm in elem_im['logical-network-map']:
                        if elem_lnm['name'].lower() == seg_name.lower():
                            if elem_lnm['type'].lower() == 'vlan':
                                return elem_lnm['segment-id']

        return 'untagged'
