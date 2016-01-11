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

import six

from ..model.ControlPlane import ControlPlane
from ..model.Tier import Tier
from ..model.Hostname import Hostname
from ..model.NetworkRef import NetworkRef

from ..model.NodeRole import NodeRole
from ..model.CPController import CPController
from ..model.CPLogging import CPLogging as KenLog
from ..model.Cidr import Cidr
from ..model.StatePersistor import StatePersistor


LOG = logging.getLogger(__name__)
_hostname_encodings = dict()


class NetworkConfigController(CPController):
    def __init__(self, instructions, model):
        super(NetworkConfigController, self).__init__(instructions)

        LOG.info('%s()' % KenLog.fcn())

        self._model = model
        self._networks = dict()
        self._cache = None

    def update(self, models, controllers):
        super(NetworkConfigController, self).update(models, controllers)

        self._model = models['NetworkConfig']

    def _initialize_cache_if_necessary(self):
        if not self._cache:
            self._cache = StatePersistor(self._models, self._controllers,
                                         persistence_file='ip_addresses.yml')

    @property
    def networks_json(self):
        global _hostname_encodings

        rv = []
        for k, n in six.iteritems(self._networks):
            n_json = dict()
            n_json['index'] = k.lower()

            if isinstance(n, Cidr):
                n_json['cidr'] = str(n.cidr)
                n_json['start-address'] = str(n.start_address)
                n_json['netmask'] = str(n.netmask)
                n_json['gateway'] = str(n.gateway)
                n_json['ip-index-start'] = n.ip_index_start
                n_json['ip-index-end'] = n.ip_index_end
            else:
                n_json['ref'] = n
            rv.append(n_json)

        return rv

    def register_network(self, node_type, intf_name, seg_name, segment):
        LOG.info('%s(): node_type="%s", intf_name="%s", seg_name="%s"' % (
                 KenLog.fcn(), node_type, intf_name, seg_name))

        key = ('%s:%s:%s' % (node_type, intf_name, seg_name)).lower()

        if key not in self._networks:
            if 'ref' in segment:
                self._networks[key] = segment['ref']

            elif 'orig-ref' in segment:
                self._networks[key] = segment['orig-ref']

            elif 'network-address' in segment:
                self._networks[key] = Cidr(
                    segment['network-address']['cidr'],
                    self._models, self._controllers)

                if 'start-address' in segment['network-address']:
                    self._networks[key].start_address = segment[
                        'network-address']['start-address']
                else:
                    segment['network-address']['start-address'] = \
                        str(self._networks[key].start_address)

                if 'gateway' in segment['network-address']:
                    self._networks[key].gateway = segment[
                        'network-address']['gateway']

            else:
                LOG.error('%s(): Unable to register network' % KenLog.fcn())

    def get_network(self, node_type, intf_name, seg_name):
        LOG.info('%s(): node_type="%s", intf_name="%s", seg_name="%s"' % (
            KenLog.fcn(), node_type, intf_name, seg_name))

        key = ('%s:%s:%s' % (node_type, intf_name, seg_name)).lower()
        LOG.debug('%s(): key="%s"' % (KenLog.fcn(), key))
        if key in self._networks:
            if isinstance(self._networks[key], Cidr):
                net = self._networks[key]

                LOG.debug('%s() -> %s' % (KenLog.fcn(), net))
                return net

            network_ref = NetworkRef.normalize(self._networks[key])
            value = self._networks[network_ref]

            LOG.debug('%s() -> %s' % (KenLog.fcn(), value))
            return value

        LOG.debug('%s() -> None' % KenLog.fcn())
        return None

    def get_network_by_reference(self, reference):
        LOG.info('%s(): reference="%s"' % (KenLog.fcn(), reference))

        if reference in self._networks:
            ref = NetworkRef.normalize(reference)
            value = self._networks[ref]

            LOG.debug('%s() -> %s' % (KenLog.fcn(), value))
            return value

        LOG.debug('%s() -> None' % KenLog.fcn())
        return None

    def get_logical_network(self, pool_name, mnemonic):
        LOG.info('%s(): pool_name="%s", mnemonic="%s"' % (
            KenLog.fcn(), pool_name, mnemonic))

        for elem_li in self._model['logical-interfaces']:
            if elem_li['pool-name'].lower() == pool_name.lower():
                for elem_ln in elem_li['logical-networks']:
                    for elem_nt in elem_ln['network-traffic']:
                        if elem_nt['name'] == mnemonic:
                            LOG.debug('%s() -> %s' % (KenLog.fcn(), elem_ln))
                            return elem_ln

        if pool_name.lower() != 'global':
            return self.get_logical_network('GLOBAL', mnemonic)

        LOG.debug('%s() -> None' % KenLog.fcn())
        return None

    def get_network_interface(self, pool_name, mnemonic):
        LOG.info('%s(): pool_name="%s", mnemonic="%s"' % (
            KenLog.fcn(), pool_name, mnemonic))

        for elem_li in self._model['logical-interfaces']:
            if elem_li['pool-name'].lower() == pool_name.lower():
                for elem_ln in elem_li['logical-networks']:
                    for elem_nt in elem_ln['network-traffic']:
                        if elem_nt['name'] == mnemonic:
                            return elem_li['name']

        if pool_name.lower() != 'global':
            return self.get_network_interface('GLOBAL', mnemonic)

        LOG.debug('%s() -> None' % KenLog.fcn())
        return None

    def _make_cache_index(self, pool_name, node_type, member, ln_name):
        index = '%s:%s:%s:%s' % (pool_name, node_type, member, ln_name)
        return index.lower()

    def get_ip_info(self, controllers, node_type, logical_network, interface,
                    member, pool_name, ln_name):
        LOG.info('%s(): node_type="%s", member="%s", pool_name="%s", '
                 'ln_name="%s"' % (KenLog.fcn(), node_type, member, pool_name,
                                   ln_name))

        self._initialize_cache_if_necessary()

        env_controller = controllers['EnvironmentConfig']
        ln_name = logical_network['name']

        index = self._make_cache_index(pool_name, node_type, member, ln_name)

        cached_info = self._cache.recall_info([index])
        if cached_info:
            ip_addr = cached_info['ip_address']
            netmask = cached_info['netmask']
            gateway = cached_info['gateway']

            LOG.debug('%s() -> %s, %s, %s' % (
                KenLog.fcn(), ip_addr, netmask, gateway))
            return ip_addr, netmask, gateway

        network = self.get_network(
            node_type, interface, logical_network['name'])

        if not network:
            env_logical_network = env_controller.get_logical_network(
                node_type, interface, ln_name)

            if not env_logical_network:
                LOG.debug('%s() -> None, None, None' % KenLog.fcn())
                return None, None, None

            self.register_network(
                node_type, interface, env_logical_network['name'],
                env_logical_network)

            network = self.get_network(
                node_type, interface, env_logical_network['name'])

        if not network:
            LOG.debug('%s() -> None, None, None' % KenLog.fcn())
            return None, None, None

        ip_addr = network.get_next_address()
        netmask = network.netmask
        gateway = network.gateway

        elem = dict()
        elem['ip_address'] = str(ip_addr)
        elem['netmask'] = str(netmask)
        elem['gateway'] = str(gateway)

        cache_info = dict()
        cache_info[index] = elem

        self._cache.persist_info(cache_info)

        LOG.debug('%s() -> %s, %s, %s' % (
            KenLog.fcn(), ip_addr, netmask, gateway))
        return ip_addr, netmask, gateway

    def get_controller_node_address(self, elem_cp, t_id, hostname):
        LOG.info('%s(): hostname="%s"' % (KenLog.fcn(), hostname))

        host_enc = NetworkConfigController.decode_hostname(hostname)
        m_id = host_enc['member-id'].replace('M', '')
        mnemonic = host_enc['network-ref']

        for k1, elem_nt in six.iteritems(elem_cp['network-topology']):
            if k1 == mnemonic:
                for k2, t in six.iteritems(elem_nt):
                    if int(k2) == int(t_id):
                        for k3, elem_m in six.iteritems(t):
                            if k3.lower() == m_id.lower():
                                return elem_m['ip-address']

        return None

    def get_controller_node_netmask(self, elem_cp, t_id, hostname):
        LOG.info('%s(): hostname="%s"' % (KenLog.fcn(), hostname))

        host_enc = NetworkConfigController.decode_hostname(hostname)
        m_id = host_enc['member-id'].replace('M', '')
        mnemonic = host_enc['network-ref']

        for k1, elem_nt in six.iteritems(elem_cp['network-topology']):
            if k1 == mnemonic:
                for k2, t in six.iteritems(elem_nt):
                    if int(k2) == int(t_id):
                        for k3, elem_m in six.iteritems(t):
                            if k3.lower() == m_id.lower():
                                return elem_m['netmask']

        return None

    @staticmethod
    def get_hostname_encodings():
        global _hostname_encodings
        return _hostname_encodings

    @staticmethod
    def decode_hostname(hostname):
        global _hostname_encodings

        LOG.info('%s(): hostname="%s"' % (KenLog.fcn(), hostname))

        uc_hostname = hostname.upper()

        if uc_hostname in _hostname_encodings:
            return _hostname_encodings[uc_hostname]

        msg = 'Could not decode hostname "%s"' % hostname
        LOG.error('Could not decode hostname "%s"' % hostname)
        raise ValueError(msg)

    def _encode_hostname(self, hostname, args):
        global _hostname_encodings

        LOG.info('%s()' % KenLog.fcn())
        _hostname_encodings[hostname.upper()] = args

    def get_hostname(self, args):
        LOG.info('%s()' % KenLog.fcn())

        svc_controller = self._controllers['Service']

        if 'service_name' in args:
            args['service_name'] = svc_controller.name_to_mnemonic(
                args['service_name'])

        if args['node_role'] == NodeRole.CONTROLLER_NODE:
            hostname, enc = self._get_hostname_for_controller_node(args)

        elif args['node_role'] == NodeRole.NODE_SERVICE:
            hostname, enc = self._get_hostname_for_node_service(args)

        elif args['node_role'] == NodeRole.SERVICE_TIER:
            hostname, enc = self._get_hostname_for_service_tier(args)

        elif args['node_role'] == NodeRole.RESOURCE_SERVICE_TIER:
            hostname, enc = self._get_hostname_for_resource_service_tier(args)

        elif args['node_role'] == NodeRole.RESOURCE_CLUSTER:
            hostname, enc = self._get_hostname_for_resource_cluster(args)

        elif args['node_role'] == NodeRole.RESOURCE_NODE:
            hostname, enc = self._get_hostname_for_resource_node(args)

        elif args['node_role'] == NodeRole.VIRTUAL_MACHINE:
            hostname, enc = self._get_hostname_for_virtual_machine(args)

        else:
            LOG.info('%s() -> None' % KenLog.fcn())
            nr = args['node_role']
            msg = 'Unknown node role for hostname generation: "%s"' % nr
            raise ValueError(msg)

        if hostname:
            enc['host-type'] = NodeRole.to_type(args['node_role'])
            self._encode_hostname(hostname, enc)

            LOG.info('%s() -> %s' % (KenLog.fcn(), hostname))
        else:
            LOG.info('%s() -> None' % KenLog.fcn())

        return hostname

    def _get_hostname_for_controller_node(self, args):
        LOG.info('%s()' % KenLog.fcn())

        if str(args['member_id']).upper() == 'VIP':
            return None, None

        member_id = 'M%d' % int(args['member_id'])

        cp_ref = args['cp_type'].upper()
        if cp_ref == 'RCP':
            cp_ref += '%02d' % int(args['cp_id'])

        name = '%s-%s-T%d-%s-%s' % (
            args['cloud_nickname'].upper(), cp_ref, int(args['tier_id']),
            member_id, args['network_ref'].upper())

        enc = dict()
        enc['cloud-nickname'] = '%s' % args['cloud_nickname'].upper()
        enc['control-plane-ref'] = cp_ref
        enc['tier-id'] = 'T%d' % int(args['tier_id'])
        enc['member-id'] = member_id
        enc['network-ref'] = args['network_ref'].upper()
        enc['network-intf'] = None
        enc['vlan-ref'] = None
        enc['service-ref'] = None
        enc['node-type'] = None
        enc['node-id'] = None
        enc['vm-name'] = None

        return name, enc

    def _get_hostname_for_node_service(self, args):
        LOG.info('%s()' % KenLog.fcn())

        member_id = 'VIP'
        if str(args['member_id']).upper() != 'VIP':
            member_id = 'M%d' % int(args['member_id'])

        cp_ref = args['cp_type'].upper()
        if cp_ref == 'RCP':
            cp_ref += '%02d' % int(args['cp_id'])

        name = '%s-%s-T%s-%s-%s-%s' % (
            args['cloud_nickname'].upper(), cp_ref, args['tier_id'],
            member_id, args['service_name'].upper(),
            args['network_ref'].upper())

        vm_ref = args.get('vm_name', None)
        if vm_ref:
            vm_ref = vm_ref.upper()

        enc = dict()
        enc['cloud-nickname'] = '%s' % args['cloud_nickname'].upper()
        enc['control-plane-ref'] = cp_ref
        enc['tier-id'] = 'T%d' % int(args['tier_id'])
        enc['member-id'] = member_id
        enc['network-ref'] = args['network_ref'].upper()
        enc['network-intf'] = None
        enc['vlan-ref'] = None
        enc['service-ref'] = args['service_name'].upper()
        enc['node-type'] = None
        enc['node-id'] = None
        enc['vm-name'] = vm_ref

        return name, enc

    def _get_hostname_for_service_tier(self, args):
        LOG.info('%s()' % KenLog.fcn())

        if str(args['member_id']).upper() != 'VIP':
            return None, None

        vlan_tag = '-%s' % args['network_vlan']
        if (vlan_tag.lower() == '-untagged' or
                vlan_tag.lower() == '-'):
            vlan_tag = ''

        cp_ref = args['cp_type'].upper()
        if cp_ref == 'RCP':
            cp_ref += '%02d' % int(args['cp_id'])

        name = '%s-%s-T%d-VIP-%s%s' % (
            args['cloud_nickname'].upper(), cp_ref, int(args['tier_id']),
            args['network_intf'].upper(), vlan_tag)

        vm_ref = args.get('vm_name', None)
        if vm_ref:
            vm_ref = vm_ref.upper()

        enc = dict()
        enc['cloud-nickname'] = '%s' % args['cloud_nickname'].upper()
        enc['control-plane-ref'] = cp_ref
        enc['tier-id'] = 'T%d' % int(args['tier_id'])
        enc['member-id'] = 'VIP'
        enc['network-ref'] = None
        enc['network-intf'] = args['network_intf'].upper()
        enc['vlan-ref'] = vlan_tag.replace('-', '')
        enc['service-ref'] = None
        enc['node-type'] = None
        enc['node-id'] = None
        enc['vm-name'] = vm_ref

        return name, enc

    def _get_hostname_for_resource_service_tier(self, args):
        LOG.info('%s()' % KenLog.fcn())

        cp_ref = args['rc_type'].upper()
        if cp_ref == 'RCP':
            cp_ref += '%02d' % int(args['rc_id'])

        name = '%s-%s-T%d-M%d-NETPXE' % (
            args['cloud_nickname'].upper(), cp_ref, int(args['tier_id']),
            int(args['member_id']))

        enc = dict()
        enc['cloud-nickname'] = '%s' % args['cloud_nickname'].upper()
        enc['control-plane-ref'] = cp_ref
        enc['tier-id'] = 'T%d' % int(args['tier_id'])
        enc['member-id'] = 'M%d' % int(args['member_id'])
        enc['network-ref'] = 'NETPXE'
        enc['network-intf'] = None
        enc['vlan-ref'] = None
        enc['service-ref'] = None
        enc['node-type'] = None
        enc['node-id'] = None
        enc['vm-name'] = None

        return name, enc

    def _get_hostname_for_resource_cluster(self, args):
        LOG.info('%s()' % KenLog.fcn())

        cp_ref = args['rc_type'].upper()
        if cp_ref == 'RCP':
            cp_ref += '%02d' % int(args['rc_id'])

        name = '%s-%s-%s-N%04d-NETPXE' % (
            args['cloud_nickname'].upper(), cp_ref, args['node_type'].upper(),
            int(args['node_id']))

        enc = dict()
        enc['cloud-nickname'] = '%s' % args['cloud_nickname'].upper()
        enc['control-plane-ref'] = cp_ref
        enc['tier-id'] = None
        enc['member-id'] = None
        enc['network-ref'] = 'NETPXE'
        enc['network-intf'] = None
        enc['vlan-ref'] = None
        enc['service-ref'] = None
        enc['node-type'] = args['node_type'].upper()
        enc['node-id'] = 'N%04d' % int(args['node_id'])
        enc['vm-name'] = None

        return name, enc

    def _get_hostname_for_resource_node(self, args):
        LOG.info('%s()' % KenLog.fcn())

        cp_ref = args['cp_type'].upper()
        if cp_ref == 'RCP':
            cp_ref += '%02d' % int(args['cp_id'])

        name = '%s-%s-%s-N%04d-%s' % (
            args['cloud_nickname'].upper(), cp_ref, args['node_type'].upper(),
            int(args['node_id']), args['network_ref'].upper())

        enc = dict()
        enc['cloud-nickname'] = '%s' % args['cloud_nickname'].upper()
        enc['control-plane-ref'] = cp_ref
        enc['tier-id'] = None
        enc['member-id'] = None
        enc['network-ref'] = args['network_ref'].upper()
        enc['network-intf'] = None
        enc['vlan-ref'] = None
        enc['service-ref'] = None
        enc['node-type'] = args['node_type'].upper()
        enc['node-id'] = 'N%04d' % int(args['node_id'])
        enc['vm-name'] = None

        return name, enc

    def _get_hostname_for_virtual_machine(self, args):
        LOG.info('%s()' % KenLog.fcn())

        if str(args['member_id']).upper() == 'VIP':
            return None, None

        vm_ref = args['vm_name'].upper()

        cp_ref = args['cp_type'].upper()
        if cp_ref == 'RCP':
            cp_ref += '%02d' % int(args['cp_id'])

        member_id = 'M%d' % int(args['member_id'])

        name = '%s-%s-%s-T%d-%s-%s' % (
            args['cloud_nickname'].upper(), vm_ref, cp_ref,
            int(args['tier_id']), member_id, args['network_ref'].upper())

        enc = dict()
        enc['cloud-nickname'] = '%s' % args['cloud_nickname'].upper()
        enc['control-plane-ref'] = cp_ref
        enc['tier-id'] = 'T%d' % int(args['tier_id'])
        enc['member-id'] = member_id
        enc['network-ref'] = args['network_ref'].upper()
        enc['network-intf'] = args['network_intf']
        enc['vlan-ref'] = None
        enc['service-ref'] = None
        enc['node-type'] = None
        enc['node-id'] = None
        enc['vm-name'] = vm_ref

        return name, enc

    def _get_segment(self, cloud, pool_name, logical_network_name):
        LOG.info('%s()' % KenLog.fcn())

        for network in cloud.networks:
            if network.pool_name.lower() == pool_name.lower():
                for segment in network.segments:
                    for ln in segment.logical_networks:
                        tokens = logical_network_name.split('-')
                        lnn = tokens[0]
                        if ln.name.lower() == lnn.lower():
                            return segment

        if pool_name != 'GLOBAL':
            return self._get_segment(cloud, 'GLOBAL', logical_network_name)

        return None

    def get_service_tier_address(self, nt_model, elem_cp, hostname):
        host_enc = self.decode_hostname(hostname)

        if host_enc['vlan-ref']:
            vlan = host_enc['vlan-ref']
        else:
            vlan = 'untagged'

        interface = host_enc['network-intf']
        tier = host_enc['tier-id'][1:]
        member = host_enc['member-id']

        mnemonics = self.get_mnemonics_from_interface(
            nt_model, interface, vlan)

        for k1, elem_nt in six.iteritems(elem_cp['network-topology']):
            for mnemonic in mnemonics:
                if k1 == mnemonic:
                    for k2, elem_t in six.iteritems(elem_nt):
                        if int(k2) == int(tier):
                            for k3, elem_m in six.iteritems(elem_t):
                                if k3.lower() == member.lower():
                                    return elem_m['ip-address']

        return None

    def get_service_tier_vip_address(self, elem_cp, elem_t, network):
        tier = elem_t['id']
        member = 'vip'

        for k1, elem_nt in six.iteritems(elem_cp['network-topology']):
            if k1 == network:
                for k2, elem_t in six.iteritems(elem_nt):
                    if int(k2) == int(tier):
                        for k3, elem_m in six.iteritems(elem_t):
                            if k3.lower() == member.lower():
                                return elem_m['ip-address']

        return None

    def get_mnemonics_from_interface(self, nt_model, interface, vlan):
        values = []

        for elem_li in self._model['logical-interfaces']:
            if elem_li['name'].lower() == interface.lower():
                for elem_ln in elem_li['logical-networks']:
                    if self.is_logical_network_match(
                            nt_model, 'ccn', elem_li, elem_ln, vlan):
                        for elem_nt in elem_ln['network-traffic']:
                            values.append(elem_nt['name'])

        return values

    def is_logical_network_match(self, nt_model, nt, elem_li, elem_ln, vlan):
        for elem_nt in nt_model:
            if elem_nt['name'].lower() != nt.lower():
                continue

            for elem_im in elem_nt['interface-map']:
                if elem_im['name'].lower() == elem_li['name'].lower():
                    for elem_lnm in elem_im['logical-network-map']:
                        if elem_lnm['name'].lower() == elem_ln['name'].lower():
                            if 'segment-id' in elem_lnm:
                                if vlan.lower() == elem_lnm[
                                        'segment-id'].lower():
                                    return True
                            else:
                                if (vlan.lower() == 'untagged' or
                                        len(vlan) == 0):
                                    return True

        return False

    def get_resource_node_address(self, elem_cp, hostname):
        if not elem_cp['resource-nodes']:
            return None

        for net, elem_rn in six.iteritems(elem_cp['resource-nodes']):
            if 'allocations' not in elem_rn:
                continue

            for elem_a in elem_rn['allocations']:
                if elem_a['name'] == hostname:
                    return elem_a['ip-address']

        return None

    def get_service_tier_hosts(self, cloud_model, elem_cp, elem_t,
                               current_svc, relationship_svc, networks=None):
        LOG.info('%s(): current_svc="%s", relationship_svc="%s"' % (
            KenLog.fcn(), current_svc, relationship_svc))

        hosts = None
        vips = None

        ca_controller = self._controllers['CloudArchitecture']
        cp_name = ca_controller.get_cp_name(elem_cp)

        override = ca_controller.get_consumed_services_override(
            elem_t, current_svc, relationship_svc)

        if override:
            LOG.info('%s(): using override: %s' % (KenLog.fcn(), override))

            tokens = override.split('-')
            override_cp = ca_controller.get_cp(cloud_model, tokens[1])
            override_cp_name = ca_controller.get_cp_name(override_cp)
            override_tier_id, override_tier = ca_controller.get_tier(
                cloud_model, override_cp_name, tokens[2])

            hosts, vips = self.get_service_hosts_for_cp_tier(
                cloud_model, override_cp_name, override_tier_id,
                relationship_svc, networks)

        if not hosts:
            LOG.debug('%s(): use current cp and current tier' % KenLog.fcn())
            hosts, vips = self.get_service_hosts_for_cp_tier(
                cloud_model, cp_name, elem_t['id'], relationship_svc, networks)

        if not hosts:
            LOG.debug('%s(): use current cp and adjacent tiers' % KenLog.fcn())
            for tier in elem_cp['tiers']:
                if tier['id'] != elem_t['id']:
                    hosts, vips = self.get_service_hosts_for_cp_tier(
                        cloud_model, cp_name, tier['id'], relationship_svc,
                        networks)

                    if hosts:
                        break

        if not hosts:
            cp_name = ca_controller.get_cp_name(elem_cp)
            if cp_name.lower() != 'ccp':
                cur_cp = ca_controller.get_cp(cloud_model, 'ccp')
                for cur_t in cur_cp['tiers']:
                    LOG.debug('%s(): use CCP and tier %s' %
                              (KenLog.fcn(), cur_t['id']))
                    hosts, vips = self.get_service_hosts_for_cp_tier(
                        cloud_model, 'CCP', cur_t['id'], relationship_svc,
                        networks)

                    if hosts:
                        break

        return hosts, vips

    def get_service_hosts_for_cp_tier(self, cloud_model, cp_id, t_id,
                                      current_svc, networks=None):
        LOG.info('%s(): cp_id="%s", t_id="%s", current_svc="%s"' % (
            KenLog.fcn(), cp_id, t_id, current_svc))

        hosts = []
        vips = []

        svc_controller = self._controllers['Service']

        for elem_cp in cloud_model['control-planes']:
            if not ControlPlane.is_active(elem_cp):
                continue

            if not ControlPlane.equals(elem_cp, cp_id):
                continue

            for elem_t in elem_cp['tiers']:
                if not Tier.is_active(elem_t):
                    continue

                if not Tier.equals(elem_t, t_id):
                    continue

                for cns in Tier.get_controller_node_services(elem_t):
                    host_enc = NetworkConfigController.decode_hostname(cns)

                    if networks and host_enc['network-ref'] not in networks:
                        continue

                    elem_s = host_enc['service-ref']
                    if svc_controller.equals(elem_s, current_svc):
                        hostname = Hostname.output_format(
                            self._instructions, cns)
                        if host_enc['member-id'].lower() == 'vip':
                            vips.append(hostname)
                        else:
                            hosts.append(hostname)

        LOG.debug('%s() -> %s, %s' % (KenLog.fcn(), hosts, vips))
        return hosts, vips
