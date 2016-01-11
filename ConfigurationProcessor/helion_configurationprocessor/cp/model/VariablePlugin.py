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
from abc import abstractmethod

from .CPLogging import CPLogging as KenLog
from .PluginBase import PluginBase


LOG = logging.getLogger(__name__)


@six.add_metaclass(ABCMeta)
class VariablePlugin(PluginBase):
    def __init__(self, version, instructions, models, controllers, slug):
        super(VariablePlugin, self).__init__(version, instructions, slug)

        LOG.info('%s()' % KenLog.fcn())

        self._models = models
        self._controllers = controllers
        self._errors = []

    @abstractmethod
    def calculate(self, payload=None):
        """ Construct a variable value
        :return: True if the building succeeded, False if it failed.  Note
        that if it fails, the plugin should throw an exception.
        """
        pass
