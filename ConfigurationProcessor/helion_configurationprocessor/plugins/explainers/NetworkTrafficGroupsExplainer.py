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

from collections import OrderedDict

from helion_configurationprocessor.cp.model.ControlPlane import ControlPlane
from helion_configurationprocessor.cp.model.Tier import Tier

from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import ExplainerPlugin
from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import ordinal
from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import pluralize
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class NetworkTrafficGroupsExplainer(ExplainerPlugin):
    def __init__(self, instructions, models, controllers):
        super(NetworkTrafficGroupsExplainer, self).__init__(
            1, instructions, models, controllers,
            'network-traffic-groups')
        LOG.info('%s()' % KenLog.fcn())

    def explain(self):
        LOG.info('%s()' % KenLog.fcn())

        fp = self._get_explainer_file()

        message = self._get_title()
        message += self._get_networks()

        fp.write('%s' % message)

        self._close_explainer_file(fp)

    def _get_title(self):
        message = '::Network Traffic Groups::\n\n'
        return message

    def _get_networks(self):
        svc_controller = self._controllers['Service']

        message = ''

        networks = OrderedDict()

        for elem_cp in self._models['CloudModel']['control-planes']:
            if not ControlPlane.is_active(elem_cp):
                continue

            for elem_t in elem_cp['tiers']:
                if not Tier.is_active(elem_t):
                    continue

                for elem_s in elem_t['services']:
                    for elem_nr in elem_s['network_refs']:
                        if elem_nr not in networks:
                            networks[elem_nr] = []

                        if elem_s['name'] not in networks[elem_nr]:
                            networks[elem_nr].append(elem_s['name'])

        for n, services in six.iteritems(networks):
            sservices = sorted(services)
            message += 'The following %s connected to the "%s" ' \
                       'traffic group:\n' % (
                           pluralize(len(sservices), 'service ' 'is',
                                                     'services are'), n)

            for elem_s in sservices:
                mnemonic = svc_controller.name_to_mnemonic(elem_s)
                name = svc_controller.mnemonic_to_name(elem_s)
                message += '    %s (%s)\n' % (mnemonic, name)

            message += '\n    and are accessed with the following:\n'

            for elem_cp in self._models['CloudModel']['control-planes']:
                if not ControlPlane.is_active(elem_cp):
                    continue

                cp_type = ControlPlane.get_name(elem_cp)

                addresses = []

                for nt, elem_nt in six.iteritems(elem_cp['network-topology']):
                    if nt.lower() != n.lower():
                        continue

                    for t, elem_t in six.iteritems(elem_nt):
                        for m, elem_m in six.iteritems(elem_t):
                            addr = cp_type

                            if m.lower() == 'vip':
                                addr += ' for VIP access on the ' \
                                        '%s tier: ' % \
                                        ordinal(int(t))
                            else:
                                addr += ' on the '\
                                        '%s member of the %s tier: ' % \
                                        (ordinal(int(m)), ordinal(int(t)))

                            addr += elem_m['ip-address']

                            addresses.append(addr)

                sorted_addresses = sorted(addresses)
                for elem_a in sorted_addresses:
                    message += '        %s\n' % elem_a

            message += '\n'

        return message

    def get_dependencies(self):
        return ['services']
