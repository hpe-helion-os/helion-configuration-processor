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


LOG = logging.getLogger(__name__)


class ServerRolesValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(ServerRolesValidator, self).__init__(
            2.0, instructions, config_files,
            'server-roles-2.0')
        self._valid = False
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())

        version = float(self.version())

        input = self._create_content(version, "server-roles")
        self._valid = self.validate_schema(input, "server_role")

        if self._valid:
            server_roles = input['server-roles']
            self._validate_names(server_roles)

        return self._valid

    def _validate_names(self, server_roles):

        #
        # Check each model is only defined once
        #
        names = set()
        for role in server_roles:
            if role['name'] in names:
                msg = ("Server Role %s is defined more than once." %
                       (role['name']))
                self.add_error(msg)
                self._valid = False
            else:
                names.add(role['name'])

    @property
    def instructions(self):
        return self._instructions

    def get_dependencies(self):
        return []
