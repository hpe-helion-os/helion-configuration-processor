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


class RingSpecificationsGenerator(GeneratorPlugin):
    def __init__(self, instructions, models, controllers):
        super(RingSpecificationsGenerator, self).__init__(
            2.0, instructions, models, controllers,
            'ring-specifications-2.0')
        LOG.info('%s()' % KenLog.fcn())

    def generate(self):
        LOG.info('%s()' % KenLog.fcn())

        self._generate_ring_specifications_info()

    def _generate_ring_specifications_info(self):
        LOG.info('%s()' % KenLog.fcn())
        self._action = KenLog.fcn()
        cloud_version = CloudModel.version(
            self._models['CloudModel'], self._version)
        ring_specifications_config = CloudModel.get(
            cloud_version, 'ring-specifications', [])
        cloud_internal = CloudModel.internal(self._models['CloudModel'])
        CloudModel.put(cloud_internal,
                       'ring-specifications',
                       ring_specifications_config)

    def get_dependencies(self):
        return ['cloud-cplite-2.0']
