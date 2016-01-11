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

from abc import ABCMeta

from .CPLogging import CPLogging as KenLog
from .CPVariables import MODEL_VERSION


LOG = logging.getLogger(__name__)


@six.add_metaclass(ABCMeta)
class PluginBase(KenLog):
    def __init__(self, version, instructions, slug):
        super(PluginBase, self).__init__(instructions)

        LOG.info('%s()' % KenLog.fcn())

        self._version = version
        self._instructions = instructions
        self._slug = slug

        self._errors = []
        self._warnings = []

        self._default_dependencies = []

    def __repr__(self):
        return 'PluginBase: %s' % self._slug

    @property
    def instructions(self):
        return self._instructions

    @property
    def slug(self):
        return self._slug

    @property
    def ok(self):
        return len(self._errors) == 0

    @property
    def warnings(self):
        return self._warnings

    def is_compatible_with_cloud(self, args):
        instructions = args[0]
        cloud_version = instructions.get('model_version', MODEL_VERSION)

        cloud_version = '%3.1f' % float(cloud_version)
        version = '%3.1f' % float(self._version)

        return str(cloud_version) == str(version)

    def get_model_version(self):
        if isinstance(self._version, float):
            return '%03.1f' % self._version
        else:
            return '%03d' % self._version

    def log_and_add_warning(self, warning):
        LOG.warning(warning)
        self.add_warning(warning)

    def add_warnings(self, warnings):
        for warning in warnings:
            self.add_warning(warning)

    def add_warning(self, warning):
        if warning not in self._warnings:
            self._warnings.append(warning)

    @property
    def errors(self):
        return self._errors

    def log_and_add_error(self, error):
        LOG.error(error)
        self.add_error(error)

    def add_errors(self, errors):
        for error in errors:
            self.add_error(error)

    def add_error(self, error):
        if error not in self._errors:
            self._errors.append(error)

    def get_dependencies(self):
        return self._default_dependencies

    def unit_test_set_dependencies(self, dependencies):
        self._default_dependencies = dependencies
