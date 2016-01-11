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

from helion_configurationprocessor.cp.model.ValidatorPlugin \
    import ValidatorPlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog
from helion_configurationprocessor.cp.model.CPSecurity \
    import CPSecurity


LOG = logging.getLogger(__name__)


class EncryptionKeyValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(EncryptionKeyValidator, self).__init__(
            1, instructions, config_files, 'encryption-key')

        LOG.info('%s()' % KenLog.fcn())

    def is_compatible_with_cloud(self, args):
        return True

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())

        if 'encryption_key' in self._instructions:
            path = self._instructions['cloud_input_path']
            status, messages = CPSecurity.validate(
                path, self._instructions['encryption_key'])

            if not status:
                message = 'The Encryption Key does not meet the following ' \
                          'requirement(s):\n#       %s' % \
                          '\n#       '.join(messages)
                self.add_error(message)
                return False

            score, msg = CPSecurity.calculate_complexity(
                self._instructions['encryption_key'])

            print('\n\nThe encryption key has a complexity score of %d ('
                  '%s)\n\n' % (score, msg))

        if ('previous_encryption_key' in self._instructions and
                'encryption_key' in self._instructions):
            if (self._instructions['encryption_key'] ==
                    self._instructions['previous_encryption_key']):
                message = 'The New Encryption Key and the Previous ' \
                          'Encryption Key must be different.'
                self.add_error(message)
                return False

        return True

    @property
    def instructions(self):
        return self._instructions

    def get_dependencies(self):
        return []
