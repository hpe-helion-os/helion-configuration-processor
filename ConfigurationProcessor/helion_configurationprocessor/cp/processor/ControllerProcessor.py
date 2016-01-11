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
import six
import logging

from ..controller.CloudConfigController import CloudConfigController

from ..model.CPProcessor import CPProcessor
from ..model.JsonConfigFile import JsonConfigFile
from ..model.YamlConfigFile import YamlConfigFile
from ..model.CPLogging import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class ControllerProcessor(CPProcessor):
    def __init__(self, instructions, models):
        super(ControllerProcessor, self).__init__(instructions, "Controller")

        LOG.info('%s()' % KenLog.fcn())

        self._models = models
        self._controllers = dict()

        self._site_path = instructions['site_input_path']

    def process(self):
        LOG.info('%s()' % KenLog.fcn())

        if not self._create_controllers():
            return False

        if not self._update_controllers():
            return False

        return True

    def _create_controllers(self):
        LOG.info('%s()' % KenLog.fcn())

        instructions = self._instructions

        self._controllers['CloudConfig'] = \
            CloudConfigController(
                instructions, self._models['CloudConfig'])

        return True

    def _update_controllers(self):
        LOG.info('%s()' % KenLog.fcn())

        return_value = True

        for controller, elem_c in six.iteritems(self._controllers):
            self._controllers[controller].update(self._models,
                                                 self._controllers)

        return return_value

    def _get_ca_topic_properties(self, file_name, topic):
        LOG.info('%s()' % KenLog.fcn())

        if file_name.endswith('.json'):
            cf = JsonConfigFile(topic, file_name)
            cf.load()

        elif file_name.endswith('.yml') or file_name.endswith('.yaml'):
            cf = YamlConfigFile(topic, file_name)
            cf.load()

        else:
            LOG.warning('Unsupported file type: %s' % file_name)
            return

        element = cf.contents

        if 'properties' not in element:
            return dict()

        return element['properties']

    def _get_ca_properties(self, file_base, topic):
        LOG.info('%s()' % KenLog.fcn())

        for suffix in ['json', 'yml', 'yaml']:
            file_name = '%s.%s' % (file_base, suffix)
            s_path = os.path.join(self._site_path, file_name)
            if os.path.exists(s_path) and os.path.isfile(s_path):
                return self._get_ca_topic_properties(s_path, topic)

    @property
    def models(self):
        return self._models

    @models.setter
    def models(self, models):
        self._models = models

    @property
    def controllers(self):
        return self._controllers
