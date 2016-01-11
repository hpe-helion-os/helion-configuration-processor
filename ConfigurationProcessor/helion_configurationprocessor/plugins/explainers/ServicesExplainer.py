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


class ServicesExplainer(ExplainerPlugin):
    def __init__(self, instructions, models, controllers):
        super(ServicesExplainer, self).__init__(
            1, instructions, models, controllers,
            'services')
        LOG.info('%s()' % KenLog.fcn())

    def explain(self):
        LOG.info('%s()' % KenLog.fcn())

        fp = self._get_explainer_file()

        message = self._get_title()
        message += self._get_services()

        fp.write('%s' % message)

        self._close_explainer_file(fp)

    def _get_title(self):
        message = '::Services::\n\n'
        return message

    def _get_services(self):
        svc_controller = self._controllers['Service']

        message = ''

        cp_index = 1
        for elem_cp in self._models['CloudModel']['control-planes']:
            if not ControlPlane.is_active(elem_cp):
                cp_index += 1
                continue

            t_index = 1
            for elem_t in elem_cp['tiers']:
                if not Tier.is_active(elem_t):
                    t_index += 1
                    continue

                num_services = len(elem_t['members']['vip']['services'])

                message += 'In the %s tier of the %s control plane (%s), ' \
                           'the following %s defined:\n' % \
                    (ordinal(t_index), ordinal(cp_index), elem_cp['type'],
                     pluralize(num_services, 'service is', 'services are'))

                services = sorted(elem_t['members']['1']['services'])
                for elem_s in services:
                    mnemonic = svc_controller.name_to_mnemonic(elem_s['name'])
                    name = svc_controller.mnemonic_to_name(elem_s['name'])
                    message += '    %s (%s)\n' % (mnemonic, name)

                message += '\n'

                if 'vip' in elem_t['members']:
                    services = sorted(elem_t['members']['vip']['services'])
                    num_services = len(services)
                    message += '    with VIP access to %s:\n' % (
                        pluralize(num_services, 'this service',
                                  'these services'))

                    for elem_s in services:
                        mnemonic = svc_controller.name_to_mnemonic(
                            elem_s['name'])
                        name = svc_controller.mnemonic_to_name(elem_s['name'])
                        message += '        %s (%s)\n' % (mnemonic, name)

                    message += '\n'

                t_index += 1

            cp_index += 1

        return message

    def get_dependencies(self):
        return ['cloud-structure']
