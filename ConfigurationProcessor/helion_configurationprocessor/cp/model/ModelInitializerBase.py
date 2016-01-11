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
import logging.config
from abc import ABCMeta
from abc import abstractmethod

import six

from helion_configurationprocessor.cp.model.ConfigProcess import ConfigProcess
from helion_configurationprocessor.cp.model.v2_0.CloudModel import CloudModel
from helion_configurationprocessor.cp.model.Version import Version
from CPLogging import CPLogging as KenLog

LOG = logging.getLogger(__name__)


@six.add_metaclass(ABCMeta)
class ModelInitializerBase(object):
    def __init__(self, version, instructions, config_files, models, cloud_path,
                 site_path):
        super(ModelInitializerBase, self).__init__()

        self._version = version
        self._instructions = instructions
        self._models = models
        self._config_files = config_files
        self._cloud_path = cloud_path
        self._site_path = site_path

    @abstractmethod
    def load_models(self):
        return None

    def load_model(self, name, file_name=None, file_type=None):
        if file_type:
            file_name = self._models['CloudDescription']['cloud'].get(
                file_type, None)

        if not file_name:
            return

        file_path = os.path.dirname(file_name)
        if len(file_path) == 0:
            file_path = self._cloud_path
        else:
            file_path = os.path.join(self._cloud_path, file_path)
            file_name = os.path.basename(file_name)

        p = ConfigProcess(name, self._site_path, file_path, file_name)

        if p.load():
            self._models[name] = p.model
        else:
            print(p.errors)
            self._models[name] = None
            raise Exception('Could not load model "%s"' % name)

    def version(self):
        return Version.normalize(Version.get(
            self._instructions['cloud_input_path']))

    def load_empty_model(self, name, config_key):
        LOG.info('%s()' % KenLog.fcn())
        if name not in self._models:
            self._models[name] = dict()
        self._models[name][config_key] = []

    def load_versioned_model(self, version, config_key, optional=False, alias=None):
        LOG.info('%s()' % KenLog.fcn())

        v = Version.normalize(version)
        config_value = self._get_config_value(v, config_key)
        if not config_value and alias:
            LOG.warn("Use of %s is deprecated, use %s instead" %
                     (alias, config_key))
            config_value = self._get_config_value(v, alias)

        if config_value:
            cloud_model = CloudModel.version(self._models['CloudModel'], v)
            cloud_model[config_key] = config_value
        elif not optional:
            raise Exception('Could not load model key "%s"' % config_key)

    def _get_config_value(self, version, config_key):
        this_version = 0.0
        for version_dict in self._config_files:
            for key, value in six.iteritems(version_dict):
                if key.lower() == 'version':
                    this_version = value
            if float(this_version) == float(version):
                for key, value in six.iteritems(version_dict):
                    if key.lower() == config_key.lower():
                        return value
        return None
