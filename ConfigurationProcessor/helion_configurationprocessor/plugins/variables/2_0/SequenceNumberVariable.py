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

from helion_configurationprocessor.cp.model.VariablePlugin \
    import VariablePlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class SequenceNumberVariable(VariablePlugin):
    def __init__(self, instructions, models, controllers):
        super(SequenceNumberVariable, self).__init__(
            2.0, instructions, models, controllers,
            'sequence-number-2.0')

        self._current_value = None

        LOG.info('%s()' % KenLog.fcn())

    def calculate(self, payload=None):
        LOG.info('%s()' % KenLog.fcn())

        if not payload:
            payload = dict()

        if 'start-value' not in payload:
            self.add_error('start-value is a required property')
            return None

        if not self._current_value:
            self._current_value = int(payload['start-value'])

        return self._calculate()

    def _calculate(self):
        LOG.info('%s()' % KenLog.fcn())

        value = self._current_value
        self._current_value += 1
        LOG.debug('%s() -> %s' % (KenLog.fcn(), value))
        return value

    @property
    def instructions(self):
        return self._instructions

    @property
    def models(self):
        return self._models

    @property
    def controllers(self):
        return self._controllers
