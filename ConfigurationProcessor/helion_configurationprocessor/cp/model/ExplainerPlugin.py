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

from abc import ABCMeta
from abc import abstractmethod

from .CPLogging import CPLogging as KenLog
from .PluginBase import PluginBase

from Version import Version

vowels = ['a', 'e', 'i', 'o', 'u', 'h']

LOG = logging.getLogger(__name__)


def ordinal(n):
    return "%d%s" % (
        n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


def pluralize(n, s, p):
    return s if n == 1 or n == -1 else p


def aoran(token, is_upper):
    if token.lower()[0] in vowels:
        if is_upper:
            return 'An'
        else:
            return 'an'

    else:
        if is_upper:
            return 'A'
        else:
            return 'a'


@six.add_metaclass(ABCMeta)
class ExplainerPlugin(PluginBase):
    def __init__(self, version, instructions, models, controllers, slug):
        super(ExplainerPlugin, self).__init__(version, instructions, slug)

        LOG.info('%s()' % KenLog.fcn())

        self._models = models
        self._controllers = controllers
        self._explainer_file = self._get_explainer_file()

    @abstractmethod
    def explain(self):
        """ Take the model and construct some output according to the
        instructions
        :return: True if the building succeeded, False if it failed.  Note
        that if it fails, the plugin should throw an exception.
        """
        pass

    def _get_explainer_file(self):
        cloud_config = self._controllers['CloudConfig']
        path = cloud_config.get_output_path(self._models)
        file_name = '%s/CloudExplanation.txt' % path

        if os.path.exists(file_name):
            fp = open(file_name, 'a')
        else:
            print('Explainer file %s Created' % file_name)
            fp = open(file_name, 'w')

        return fp

    def version(self):
        return Version.get(self.instructions['cloud_input_path'])

    def _close_explainer_file(self, fp):
        fp.close()

    @property
    def models(self):
        return self._models

    @property
    def controllers(self):
        return self._controllers
