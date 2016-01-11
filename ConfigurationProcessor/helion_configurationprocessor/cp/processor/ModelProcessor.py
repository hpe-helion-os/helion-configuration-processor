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
import importlib
import logging
import traceback

from ..model.CloudDescription import CloudDescription

from ..model.CPProcessor import CPProcessor
from ..model.ConfigProcess import ConfigProcess
from ..model.CPLogging import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class ModelProcessor(CPProcessor):
    def __init__(self, instructions, config_files):
        super(ModelProcessor, self).__init__(instructions,
                                             "Model")

        LOG.info('%s()' % KenLog.fcn())

        self._models = dict()
        self._controllers = dict()
        self._site_path = instructions['site_input_path']

        self._cloud_path = os.path.dirname(
            instructions['cloud_input_path'])

        self._cloud_config_path = os.path.basename(
            instructions['cloud_input_path'])

        self._config_files = config_files

    def process(self):
        LOG.info('%s()' % KenLog.fcn())

        if not self._load_models():
            return False

        return True

    def _load_models(self):
        LOG.info('%s()' % KenLog.fcn())

        self._errors = []

        self._models['CloudModel'] = dict()

        print "about to load CloudDescription %s" % (self._cloud_config_path)
        self._load_model('CloudDescription',
                         file_name=self._cloud_config_path)

        version = CloudDescription.get_version(
            self._models['CloudDescription'])
        version = '%3.1f' % version

        class_version = version.replace('.', '_')
        class_name = 'model_%s' % class_version

        module_name = 'helion_configurationprocessor'
        module_name += '.cp'
        module_name += '.processor'
        module_name += '.models'
        module_name += '.%s' % class_name

        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)

        instance = class_(version, self._instructions, self._config_files,
                          self._models, self._cloud_path, self._site_path)

        try:
            instance.load_models()
        except Exception as e:
            msg = 'ModelProcessor encountered an exception: %s\n' % e
            self.log_and_print_error(KenLog.fcn(), msg
                                     + traceback.format_exc())
            self.add_error(e)

        return len(self._errors) == 0

    def _load_model(self, name, file_name=None, file_type=None):
        LOG.info('%s(): name="%s", file_name="%s", file_type="%s"' % (
            KenLog.fcn(), name, file_name, file_type))

        if file_type:
            file_name = self._models['CloudDescription']['cloud'].get(
                file_type, None)

        if not file_name:
            return

        file_path = os.path.dirname(file_name)
        if len(file_path) == 0:
            file_path = self._cloud_path
        else:
            file_name = os.path.basename(file_name)

        p = ConfigProcess(name, self._site_path, file_path, file_name)

        if p.load():
            print "loading %s" % name
            self._models[name] = p.model
        else:
            print "error on load %s" % file_name
            self.add_errors(p.errors)

    def _add_element(self, model, topic, element, sort_key):
        if topic not in model:
            model[topic] = []

        topic_model = model[topic]
        topic_model.append(element)
        topic_model = sorted(topic_model, key=lambda x: x[sort_key].lower())
        model[topic] = topic_model

    def add_network_traffic(self, model, nt):
        LOG.info('%s()' % KenLog.fcn())
        self._add_element(model, 'network-traffic', nt, 'mnemonic')

    @property
    def models(self):
        return self._models
