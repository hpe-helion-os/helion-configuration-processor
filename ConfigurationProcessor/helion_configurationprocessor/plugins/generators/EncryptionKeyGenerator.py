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

from helion_configurationprocessor.cp.model.GeneratorPlugin \
    import GeneratorPlugin
from helion_configurationprocessor.cp.model.CPSecurity \
    import CPSecurity
from helion_configurationprocessor.cp.model.StatePersistor \
    import StatePersistor
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class EncryptionKeyGenerator(GeneratorPlugin):
    def __init__(self, instructions, models, controllers):
        super(EncryptionKeyGenerator, self).__init__(
            1, instructions, models, controllers,
            'encryption-key')

        LOG.info('%s()' % KenLog.fcn())

    def is_compatible_with_cloud(self, args):
        return True

    def generate(self):
        LOG.info('%s()' % KenLog.fcn())

        prev_encryption_key = self._instructions.get(
            'previous_encryption_key', None)

        encryption_key = self._instructions.get(
            'encryption_key', None)

        if not prev_encryption_key:

            if not encryption_key and self._get_encrypted_validator():
                message = 'Encrypted values detected.  You need to ' \
                          'run with -e specified'
                self.log_and_add_error(message)
                return False

            if encryption_key:
                if self._get_encrypted_validator():
                    if not self._validate_encryption_key(encryption_key):
                        message = 'The encryption key that you entered does ' \
                                  'not correctly decode the stored values. ' \
                                  'Check to make sure that you entered it ' \
                                  'correctly.'
                        self.log_and_add_error(message)
                        return False
                self._encrypt_validator(encryption_key)

            return True

        if not self._validate_encryption_key(prev_encryption_key):
            message = 'The previous encryption key that you entered does ' \
                      'not correctly decode the stored values. ' \
                      'Check to make sure that you entered it ' \
                      'correctly.'
            self.log_and_add_error(message)
            return False

        self._encrypt_validator(encryption_key)
        self._migrate_keys(prev_encryption_key, encryption_key)

        return True

    def _migrate_keys(self, prev_encryption_key, encryption_key):
        state_persistor = StatePersistor(
            self._models, self._controllers,
            persistence_file='private_data.yml')

        all_private_data = state_persistor.recall_info()

        for k, v in six.iteritems(all_private_data):
            if k == 'encryption_key_checker':
                continue

            if not self._was_persisted_value_encrypted(k):
                continue

            v = CPSecurity.decrypt(prev_encryption_key, v)
            v = CPSecurity.encrypt(encryption_key, v)

            info = {k: v}
            state_persistor.persist_info(info)

    def _validate_encryption_key(self, secret):
        value = self._get_encrypted_validator()

        if value:
            property_value = 'encryption_key_checker'

            value = CPSecurity.decrypt(secret, value)
            if value == property_value:
                return True

        return False

    def _get_encrypted_validator(self):
        state_persistor = StatePersistor(
            self._models, self._controllers,
            persistence_file='private_data.yml')

        property_name = 'encryption_key_checker'
        value = state_persistor.recall_info([property_name])
        return value

    def _encrypt_validator(self, secret):
        state_persistor = StatePersistor(
            self._models, self._controllers,
            persistence_file='private_data.yml')

        property_name = 'encryption_key_checker'
        property_value = 'encryption_key_checker'

        property_value = CPSecurity.encrypt(secret, property_value)

        info = {property_name: property_value}
        state_persistor.persist_info(info)

    def _was_persisted_value_encrypted(self, property_name):
        secure_property_name = '%s__is_secure' % property_name

        state_persistor = StatePersistor(
            self._models, self._controllers,
            persistence_file='private_data.yml')

        value = state_persistor.recall_info([secure_property_name])
        if value is None:
            return False

        return value is not None

    def get_dependencies(self):
        return []
