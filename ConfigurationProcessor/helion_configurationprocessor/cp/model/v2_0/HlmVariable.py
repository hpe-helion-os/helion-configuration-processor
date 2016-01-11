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
from stevedore import driver

from helion_configurationprocessor.cp.model.StatePersistor \
    import StatePersistor
from helion_configurationprocessor.cp.model.Version \
    import Version
from helion_configurationprocessor.cp.model.CPSecurity \
    import CPSecurity


class HlmVariable(object):
    @staticmethod
    def generate_value(instructions, models, controllers, name, value,
                       payload=None):

        if not isinstance(value, str):
            return value

        if value.count('%') != 2:
            return value

        sp = StatePersistor(models, controllers, 'private_data.yml')

        if not instructions['refresh_passwords']:
            ri = sp.recall_info([name])
            ri_e = HlmVariable.was_persisted_value_encrypted(sp, name)
            if ri and not ri_e:
                if 'encryption_key' in instructions:
                    key = instructions['encryption_key']
                    secure_value = CPSecurity.encrypt(key, ri)
                    HlmVariable.persist_value(sp, name, secure_value, True)
                return ri
            elif ri and ri_e:
                return HlmVariable.decrypt_value(ri, instructions)

        p1 = value.find('%') + 1
        p2 = value.rfind('%')
        variable_type = value[p1:p2]

        version = instructions['model_version']
        version = Version.normalize(version)
        if float(version) > 1.0:
            variable_type += '-%s' % version

        try:
            namespace = 'helion.configurationprocessor.variable'

            mgr = driver.DriverManager(
                namespace=namespace, name=variable_type, invoke_on_load=True,
                invoke_args=(instructions, models, controllers))

        except RuntimeError as e:
            return value

        value = mgr.driver.calculate(payload)

        if not mgr.driver.ok:
            msg = '@@@@ Variable %s Failed to complete for name %s:\n' % (
                  variable_type, name)
            for e in mgr.driver.errors:
                msg += '@@@@ \t%s\n' % e
            print(msg)
            return None

        if 'encryption_key' in instructions:
            key = instructions['encryption_key']
            secure_value = CPSecurity.encrypt(key, value)
            is_secure_val = True
        else:
            secure_value = value
            is_secure_val = False

        HlmVariable.persist_value(sp, name, secure_value, is_secure_val)

        return value

    @staticmethod
    def persist_value(sp, name, secure_value, is_secure_val):
        pi = {name: secure_value}
        sp.persist_info(pi)

        is_secure = '%s__is_secure' % name
        pi = {is_secure: is_secure_val}
        sp.persist_info(pi)

    @staticmethod
    def was_persisted_value_encrypted(sp, property_name):
        secure_property_name = '%s__is_secure' % property_name

        value = sp.recall_info([secure_property_name])
        if value is None:
            return False

        return value is not False

    @staticmethod
    def get_encrypted_validator(sp):
        property_name = 'encryption_key_checker'
        value = sp.recall_info([property_name])
        return value

    @staticmethod
    def decrypt_value(value, instructions):
        return CPSecurity.decrypt(instructions['encryption_key'], value)
