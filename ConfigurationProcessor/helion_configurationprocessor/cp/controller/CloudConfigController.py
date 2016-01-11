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
import grp
import pwd
import logging

from ..model.CPController import CPController
from ..model.CPLogging import CPLogging as KenLog
from ..model.JsonConfigFile import JsonConfigFile
from ..model.YamlConfigFile import YamlConfigFile


LOG = logging.getLogger(__name__)


class CloudConfigController(CPController):
    def __init__(self, instructions, model):
        super(CloudConfigController, self).__init__(instructions)

        LOG.info('%s()' % KenLog.fcn())

        self._model = model
        self._is_valid = False

    def update(self, models, controllers):
        super(CloudConfigController, self).update(models, controllers)

        self._model = models['CloudConfig']

    # Output Path: ./clouds/<cloud_name>/<cloud_version>/stage
    def get_output_path(self, models):
        LOG.info('%s()' % KenLog.fcn())

        cloud_desc = models['CloudDescription']['cloud']
        cloud_name = cloud_desc['name'].replace(' ', '_')

        path = self._instructions['cloud_output_path']
        path = path.replace('@CLOUD_NAME@', cloud_name)
        return path

    # Network Path: ./clouds/<cloud_name>/<cloud_version>/stage/net
    def get_network_path(self, models):
        LOG.info('%s()' % KenLog.fcn())

        cloud_desc = models['CloudDescription']['cloud']
        cloud_name = cloud_desc['name'].replace(' ', '_')

        path = self._instructions['network_output_path']
        path = path.replace('@CLOUD_NAME@', cloud_name)
        return path

    # Persistent Path: ./clouds/<cloud_name>/<cloud_version>/persistent_state
    def get_persistent_path(self, models):
        LOG.info('%s()' % KenLog.fcn())

        cloud_desc = models['CloudDescription']['cloud']
        cloud_name = cloud_desc['name'].replace(' ', '_')

        path = self._instructions['persistent_state']
        path = path.replace('@CLOUD_NAME@', cloud_name)
        return path

    # Deploy Path: ./clouds/<model_version>/<cloud_name>/deployment
    def get_deploy_path(self, models):
        LOG.info('%s()' % KenLog.fcn())

        cloud_desc = models['CloudDescription']['cloud']
        cloud_name = cloud_desc['name'].replace(' ', '_')

        path = self._instructions['cloud_deploy_path']
        path = path.replace('@CLOUD_NAME@', cloud_name)
        return path

    # Deploy Path: /var/lib/hlm
    def get_global_output_path(self):
        LOG.info('%s()' % KenLog.fcn())
        return self._instructions['global_output_path']

    @staticmethod
    def get_cloud_names(file_name):
        LOG.info('%s()' % KenLog.fcn())

        if file_name.endswith('.json'):
            cf = JsonConfigFile('cloudConfig', file_name)
            cf.load()

        elif file_name.endswith('.yml') or file_name.endswith('.yaml'):
            cf = YamlConfigFile('cloudConfig', file_name)
            cf.load()

        else:
            LOG.warning('Unsupported file type: %s' % file_name)
            return

        element = cf.contents

        name = element['cloud']['name'], element['cloud']['nickname']
        nickname = element['cloud']['nickname']
        nickname = nickname.replace(name, '')

        return name, nickname

    @staticmethod
    def refresh_password(models, password):
        LOG.info('%s()' % KenLog.fcn())

        if 'password-refresh' not in models['CloudDescription']:
            return False

        for elem_pr in models['CloudDescription']['password-refresh']:
            if elem_pr['name'].lower() == password.lower():
                return True

        return False

    @staticmethod
    def get_owner_user(models):
        LOG.info('%s()' % KenLog.fcn())

        if 'ownership' in models['CloudDescription']:
            ownership = models['CloudDescription']['ownership']

            user = ownership.get('user', None)
            if user:
                if user.lower() != 'current-user':
                    try:
                        user_id = pwd.getpwnam(user).pw_uid
                        return user_id
                    except Exception:
                        pass

        user_id = os.getuid()
        return user_id

    @staticmethod
    def get_owner_group(models):
        LOG.info('%s()' % KenLog.fcn())

        if 'ownership' in models['CloudDescription']:
            ownership = models['CloudDescription']['ownership']

            group = ownership.get('group', 'helion')
        else:
            group = 'helion'

        if group != 'current-group':
            try:
                group_id = grp.getgrnam(group).gr_gid
                return group_id
            except Exception:
                pass

        group_id = os.getgid()
        return group_id

    @staticmethod
    def get_permissions_dir(models):
        LOG.info('%s()' % KenLog.fcn())

        if 'permissions' in models['CloudDescription']:
            permissions = models['CloudDescription']['permissions']

            dir_perm = permissions.get('directory', '0750')
            return int(dir_perm, 8)

        return 0750

    @staticmethod
    def get_permissions_file(models):
        LOG.info('%s()' % KenLog.fcn())

        if 'permissions' in models['CloudDescription']:
            permissions = models['CloudDescription']['permissions']

            file_perm = permissions.get('file', '0640')
            return int(file_perm, 8)

        return 0640
