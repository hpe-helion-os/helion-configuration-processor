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
import logging
from abc import ABCMeta

from .JsonConfigFile import JsonConfigFile
from .YamlConfigFile import YamlConfigFile
from .CPLogging import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class ConfigProcess(object):
    __metaclass__ = ABCMeta

    def __init__(self, process_name, site_path, cloud_path, file_name=None):

        LOG.info(
            '%s(): process_name="%s", site_path="%s", cloud_path="%s", '
            'file_name="%s"' % (
                KenLog.fcn(), process_name, site_path, cloud_path, file_name))
        self._name = process_name
        self._model = dict()
        self._site_path = site_path
        self._cloud_path = cloud_path
        self._file_name = file_name
        self._errors = []

    def __repr__(self, *args, **kwargs):
        return 'ConfigProcess: name=%s' % self.name

    def load(self):
        LOG.info('%s()' % KenLog.fcn())

        paths = [self._site_path,
                 self._cloud_path]

        path = None
        for p in paths:
            fname = os.path.join(p, self._file_name)
            if os.path.exists(fname):
                path = fname
                break

        if path is None:
            self.add_error('Could not find "%s" in any of the following '
                           'paths: %s' % (self._file_name,
                                          ', '.join(paths)))
            return False

        if self._file_name.endswith('.json'):
            json_file = JsonConfigFile(self._name, path)
            json_file.load()

            if not json_file.is_valid():
                self.add_errors(json_file.errors)
                return False

            self._model = json_file.contents

        elif (self._file_name.endswith('.yaml') or
              self._file_name.endswith('.yml')):
            yaml_file = YamlConfigFile(self._name, path)
            yaml_file.load()

            if not yaml_file.is_valid():
                self.add_errors(yaml_file.errors)
                return False

            self._model = yaml_file.contents

        return True

    @property
    def name(self):
        return self._name

    @property
    def model(self):
        return self._model

    @property
    def errors(self):
        return self._errors

    def add_error(self, error):
        self._errors.append(error)

    def add_errors(self, errors):
        for error in errors:
            self._errors.append(error)
