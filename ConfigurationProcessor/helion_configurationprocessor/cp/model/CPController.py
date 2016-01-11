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


LOG = logging.getLogger(__name__)


@six.add_metaclass(ABCMeta)
class CPController(object):
    def __init__(self, instructions):
        LOG.info('%s()' % KenLog.fcn())

        self._instructions = instructions
        self._models = None
        self._controllers = None

    def update(self, models, controllers):
        self._models = models
        self._controllers = controllers

    # Unit Testing
    def inject(self, key, controller):
        if self._controllers is None:
            self._controllers = dict()

        self._controllers[key] = controller
