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
import datetime
import logging
import timeit
import traceback

from ..model.CPProcessor import CPProcessor
from ..model.CPLogging import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class CheckpointerProcessor(CPProcessor):
    def __init__(self, instructions, models, controllers):
        super(CheckpointerProcessor, self).__init__(
            instructions, "Checkpointer")

        LOG.info('%s()' % KenLog.fcn())

        self._models = models
        self._controllers = controllers

    def process(self):
        LOG.info('%s()' % KenLog.fcn())

        if not self._run_checkpointers():
            return False

        return True

    def _run_checkpointers(self):
        LOG.info('%s()' % KenLog.fcn())

        return_value = True

        cp_name = self._get_checkpoint_name()
        self._instructions['checkpoint_base'] = cp_name

        invoke_args = (self._instructions, self._models,
                       self._controllers)

        order = self.get_plugin_order(
            'checkpointer', 'checkpointers', invoke_args)

        for checkpointer in order:
            mgr = self.load_plugin('checkpointer', checkpointer, invoke_args)
            if not mgr:
                continue

            if not mgr.driver.is_compatible_with_cloud(invoke_args):
                continue

            self.start_plugin(checkpointer)

            try:
                duration = timeit.timeit(mgr.driver.checkpoint, number=1)
            except Exception as e:
                msg = 'Checkpointer %s encountered an exception: %s\n' % (
                    checkpointer, e)
                self.log_and_print_error(KenLog.fcn(), msg
                                         + traceback.format_exc())
                continue

            self.process_warnings(mgr, checkpointer)

            if not self.process_errors(mgr, checkpointer):
                continue

            self.process_artifacts(mgr, checkpointer)

            self.complete_plugin(checkpointer, duration)

        return return_value

    def _get_checkpoint_name(self):
        name = '%s' % datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        supplied_name = self._instructions.get('checkpoint_name',
                                               'none').lower()
        if len(supplied_name) > 0 and supplied_name != 'none':
            name = '%s__%s' % (name, supplied_name.replace(' ', '_'))

        return name

    @property
    def models(self):
        return self._models

    @models.setter
    def models(self, models):
        self._models = models

    @property
    def controllers(self):
        return self._controllers

    @controllers.setter
    def controllers(self, controllers):
        self._controllers = controllers
