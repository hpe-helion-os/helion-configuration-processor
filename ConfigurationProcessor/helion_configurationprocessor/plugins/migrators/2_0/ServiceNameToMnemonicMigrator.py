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

from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog
from helion_configurationprocessor.cp.model.MigratorPlugin \
    import MigratorPlugin


LOG = logging.getLogger(__name__)


class ServiceNameToMnemonicMigrator(MigratorPlugin):
    def __init__(self, instructions, models, controllers):
        super(ServiceNameToMnemonicMigrator, self).__init__(
            2.0, instructions, models, controllers,
            'service-name-to-mnemonic-2.0')
        LOG.info('%s()' % KenLog.fcn())

    def migrate(self, model_name, model):
        LOG.info('%s()' % KenLog.fcn())
        return model
        print('Migrating the "%s" model with the "%s" migrator...' % (
            model_name, self._slug))

        if model_name == 'CloudArchitecture':
            return self._migrate_cloud_architecture(model)

        if model_name == 'Regions':
            return self._migrate_regions(model)

        return model

    def _migrate_cloud_architecture(self, model):
        svc_controller = self._controllers['Service']

        for elem_sc in model['service-components']:

            for elem_r in ['advertises-to-services',
                           'consumes-services',
                           'produces-log-files',
                           'has-proxy',
                           'has-container']:
                if elem_r in elem_sc:
                    for i in range(len(elem_sc[elem_r])):
                        s = elem_sc[elem_r][i]['service-name']
                        s_mnemonic = svc_controller.name_to_mnemonic(s)
                        elem_sc[elem_r][i]['service-name'] = s_mnemonic

        return model

    def _migrate_regions(self, model):
        svc_controller = self._controllers['Service']

        for elem_cp in model['regions']:
            for elem_t in elem_cp['member-groups']:
                print "\n\n elem_t before is" + str(elem_t)
                elem_t['service-components'] \
                    = [svc_controller.name_to_mnemonic(s) for
                       s in elem_t['service-components']]
                print "\n\n elem_t after is" + str(elem_t)
            if 'resource-nodes' not in elem_cp:
                continue

            for elem_rn in elem_cp['resource-nodes']:
                if 'service-components' in elem_rn:
                    elem_rn['services-components'] = \
                        [svc_controller.name_to_mnemonic(s)
                         for s in elem_rn['service-components']]

        return model

    def applies_to(self):
        return ['CloudArchitecture',
                'Regions'
                ]

    def get_dependencies(self):
        return []
