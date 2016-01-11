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


class ResourceNodesMigrator(MigratorPlugin):
    def __init__(self, instructions, models, controllers):
        super(ResourceNodesMigrator, self).__init__(
            2.0, instructions, models, controllers,
            'resource-nodes-to-resources-2.0')
        LOG.info('%s()' % KenLog.fcn())

    def migrate(self, model_name, model):
        LOG.info('%s()' % KenLog.fcn())
        print('Migrating the "%s" model with the "%s" migrator...' % (
            model_name, self._slug))

        for cp in model['2.0']['control-planes']:
            if 'resource-nodes' in cp:
                cp['resources'] = cp['resource-nodes']
                del cp['resource-nodes']

        return model

    def applies_to(self):
        return ['CloudModel']

    def get_dependencies(self):
        return []
