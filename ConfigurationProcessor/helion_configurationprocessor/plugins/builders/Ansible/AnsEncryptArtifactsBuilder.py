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
import os
import sh
import tempfile
import logging
import logging.config

from helion_configurationprocessor.cp.model.BuilderPlugin \
    import BuilderPlugin
from helion_configurationprocessor.cp.model.BuilderPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.model.CPSecurity \
    import CPSecurity
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class AnsEncryptArtifactsBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(AnsEncryptArtifactsBuilder, self).__init__(
            1, instructions, models, controllers,
            'ans-encr-artifacts')

        LOG.info('%s()' % KenLog.fcn())

        cloud_config = controllers['CloudConfig']
        self._output_path = '%s/ansible' % cloud_config.get_output_path(models)
        self._modules = ['group_vars', 'host_vars']
        self._pw_file = tempfile.mkstemp(suffix='.pw', prefix='ans', text=True)

    def is_compatible_with_cloud(self, args):
        return True

    def build(self):
        LOG.info('%s()' % KenLog.fcn())

        if 'encryption_key' not in self._instructions:
            return True

        self._create_password_file()

        try:
            for elem_m in self._modules:
                dir_name = os.path.join(self._output_path, elem_m)
                self._encrypt_directory(dir_name)

        except Exception:
            # Need to make sure the password file is destroyed
            pass

        finally:
            self._destroy_password_file()

        return True

    def _create_password_file(self):
        pw_file_name = self._pw_file[1]
        fp = open(pw_file_name, 'w')
        fp.write(CPSecurity.decode_key(self._instructions[
            'encryption_key']))
        fp.close()

    def _destroy_password_file(self):
        pw_file_name = self._pw_file[1]
        if os.path.exists(pw_file_name):
            fp = open(pw_file_name, 'w')
            fp.write('*' * 128)
            fp.close()
            os.remove(pw_file_name)

    def _decrypt_file_contents(self, file_name):
        fp = open(file_name, 'r')
        lines = fp.readlines()
        fp.close()

        need_to_write = False
        for i in range(len(lines)):
            line = lines[i]
            if line.find('='):
                tokens = line.split()
                for t in tokens:
                    if t.endswith('='):
                        plaintext = CPSecurity.decrypt(
                            self._instructions['encryption_key'], t)

                        if plaintext is not None:
                            lines[i] = line.replace(t, plaintext)
                            need_to_write = True

        if need_to_write:
            fp = open(file_name, 'w')
            for line in lines:
                fp.write(line)
            fp.close()

    def _encrypt_file(self, file_name):
        pw_file_name = self._pw_file[1]
        pw_file_arg = '--vault-password-file=%s' % pw_file_name

        self.add_artifact(file_name, ArtifactMode.ENCRYPTED)

        sh.ansible_vault.encrypt(file_name, pw_file_arg)

    def _encrypt_directory(self, directory):
        for root, dirs, files in os.walk(directory):
            for f in files:
                file_name = os.path.join(root, f)
                if os.path.isfile(file_name):
                    self._decrypt_file_contents(file_name)
                    self._encrypt_file(file_name)

    def get_dependencies(self):
        return ['ans-host-vars-2.0',
                'ans-group-vars-2.0',
                'ansible-all-vars-2.0',
                'ansible-hosts-2.0']
