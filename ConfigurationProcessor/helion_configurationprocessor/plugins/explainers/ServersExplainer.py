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
import six
import logging
import logging.config

from helion_configurationprocessor.cp.model.Server import Server

from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import ExplainerPlugin
from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import ordinal
from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import aoran
from helion_configurationprocessor.cp.controller.NetworkConfigController \
    import NetworkConfigController
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class ServersExplainer(ExplainerPlugin):
    def __init__(self, instructions, models, controllers):
        super(ServersExplainer, self).__init__(
            1, instructions, models, controllers,
            'servers')
        LOG.info('%s()' % KenLog.fcn())

    def explain(self):
        LOG.info('%s()' % KenLog.fcn())

        fp = self._get_explainer_file()

        message = self._get_title()
        message += self._get_servers()

        fp.write('%s' % message)

        self._close_explainer_file(fp)

    def _get_title(self):
        message = '::Servers::\n\n'
        return message

    def _get_server(self, nt_controller, server):
        elem_a = server['allocations']
        if 'hostname' not in elem_a:
            return
        cp_type = server['control-plane'].lower()
        message = ''

        message += '%s "%s %s" server has been allocated to the %s ' \
                   'control plane ' % (
                       aoran(server['vendor'], True),
                       server['vendor'], server['model'],
                       cp_type)

        node_type = nt_controller.get(
            server['node-type-elements']['type'])

        if server['member']:
            member = int(server['member'].replace('M', ''))
            tier = int(server['tier'].replace('T', ''))

            message += 'as %s "%s"\nin the %s member of the %s tier. ' % \
                       (aoran(node_type.friendly_name, False),
                        node_type.friendly_name,
                        ordinal(member), ordinal(tier))

        else:
            message += 'as %s "%s".\n' % (
                aoran(node_type.friendly_name, False),
                node_type.friendly_name)

        message += 'It\'s hostname is "%s" and\nit\'s in the "%s" ' \
                   'failure zone. ' % (
                       elem_a['hostname'], server['failure-zone'])
        message += 'It\'s PXE address is "%s".\n' % (
            server['pxe-ip-addr'])

        message += '\n'

        for li, elem_li in six.iteritems(elem_a['logical-interfaces']):
            message += ' ' * 4
            message += 'This server has a logical interface "%s".\n' % li

            if 'machine-info' in elem_li:
                elem_mi = elem_li['machine-info']

                if ('nic-bonding' in elem_mi and
                        'bond-name' in elem_mi['nic-bonding']):
                    elem_nb = elem_mi['nic-bonding']

                    elem_ni = elem_mi['nic-interface']

                    message += ' ' * 8
                    message += 'This interface uses NIC Bonding and ' \
                               'the bond name is "%s".\n' % (
                                   elem_nb['bond-name'],)

                    if 'ethernet' in elem_ni:
                        elem_e = elem_ni['ethernet']

                        message += ' ' * 12
                        message += 'The bond includes the physical ' \
                                   'ethernet ports: "%s".\n' % (
                                       ', '.join(
                                           elem_e['interface-ports']))

                    else:
                        elem_be = elem_ni['bus-enumeration']

                        for elem_ip in elem_be['interface-ports']:
                            message += ' ' * 12
                            message += 'The bond includes an enumeration ' \
                                       'where PCI Bus Address "%s"\n' % (
                                           elem_ip['bus-address'],)

                            message += ' ' * 16
                            message += 'is bound to port ' \
                                       '"%s" using label "%s".\n' % (
                                           elem_ip['port'],
                                           elem_ip['label'])

                else:
                    elem_ni = elem_mi['nic-interface']

                    if 'ethernet' in elem_ni:
                        elem_e = elem_ni['ethernet']
                        message += ' ' * 8
                        message += 'This interface is bound to the ' \
                                   'physical ethernet port "%s".\n' % (
                                       elem_e['interface-ports'][0],)

                    else:
                        elem_be = elem_ni['bus-enumeration']
                        elem_ip = elem_be['interface-ports'][0]

                        message += ' ' * 8
                        message += 'The interface includes an ' \
                                   'enumeration where PCI Bus ' \
                                   'Address "%s"\n' % (
                                       elem_ip['bus-address'],)

                        message += ' ' * 12
                        message += 'is bound to port ' \
                                   '"%s" using label "%s".\n' % (
                                       elem_ip['port'], elem_ip['label'])

                networks = sorted(elem_li['networks'])
                for elem_n in networks:
                    ip_host = elem_a['hostname'].replace('NETPXE', elem_n)
                    ip_addr = self._get_ip_addr(ip_host)
                    vlan = self._get_vlan(
                        elem_a['hostname'],
                        server['node-type-elements']['type'],
                        li, elem_n)

                    message += ' ' * 8

                    if vlan:
                        message += 'The "%s" traffic group ' \
                                   'is on VLAN "%s" and ' \
                                   'is bound to the IP Address "%s"\n' % (
                                       elem_n, vlan, ip_addr)
                    else:
                        message += 'The "%s" traffic group ' \
                                   'is not on a VLAN ' \
                                   'and is bound to the IP Address ' \
                                   '"%s"\n' % (elem_n, ip_addr)
        return message

    def _get_servers(self):
        nt_controller = self._controllers['NodeType']
        cloud_model = self._models['CloudModel']
        message = ''
        for elem_s in self._models['CloudModel']['servers']:
            if not Server.is_active(cloud_model, elem_s):
                continue
            if 'allocations' not in elem_s:
                continue
            server_message = self._get_server(nt_controller, elem_s)
            message += server_message
            message += '\n'

        return message

    def _get_ip_addr(self, hostname):
        cloud_model = self._models['CloudModel']
        for elem_cs in cloud_model['config-sets']:
            for elem_v in elem_cs['vars']:
                if elem_v['group'] != hostname:
                    continue

                return elem_v['properties']['host-info']['address']

        return '<unknown>'

    def _get_vlan(self, hostname, node_type, interface, network):
        net_controller = self._controllers['NetworkConfig']
        env_controller = self._controllers['EnvironmentConfig']

        host_enc = NetworkConfigController.decode_hostname(hostname)
        pool_name = host_enc['control-plane-ref']

        elem_nln = net_controller.get_logical_network(pool_name, network)
        if not elem_nln:
            return None

        network_id = elem_nln['name']
        elem_eln = env_controller.get_logical_network(
            node_type, interface, network_id)

        if not elem_eln:
            return None

        return elem_eln['segment-id']

    def get_dependencies(self):
        return ['network-traffic-groups']
