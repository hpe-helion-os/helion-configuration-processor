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
import string
import random

import logging
import logging.config

from helion_configurationprocessor.cp.model.VariablePlugin \
    import VariablePlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class RandomPasswordVariable(VariablePlugin):
    def __init__(self, instructions, models, controllers):
        super(RandomPasswordVariable, self).__init__(
            2.0, instructions, models, controllers,
            'random-password-2.0')
        LOG.info('%s()' % KenLog.fcn())

        random.seed()

    def calculate(self, payload=None):
        LOG.info('%s()' % KenLog.fcn())

        if not payload:
            payload = dict()

        if 'min-length' not in payload:
            payload['min-length'] = 8

        if 'max-length' not in payload:
            payload['max-length'] = 18

        if 'available-chars' not in payload:
            payload['available-chars'] = \
                string.ascii_letters + \
                string.digits

        return self._calculate(payload)

    def _calculate(self, payload):
        LOG.info('%s()' % KenLog.fcn())

        min = payload['min-length']
        max = payload['max-length']

        length = random.randint(min, max)
        length = self._normalize(length, min, max)

        value = ''.join(
            random.choice(payload['available-chars'])
            for _ in range(length))

        return value

    def _normalize(self, num, min, max):
        if num < min:
            num = min
        elif num > max:
            num = max

        return num

    @property
    def instructions(self):
        return self._instructions

    @property
    def models(self):
        return self._models

    @property
    def controllers(self):
        return self._controllers
