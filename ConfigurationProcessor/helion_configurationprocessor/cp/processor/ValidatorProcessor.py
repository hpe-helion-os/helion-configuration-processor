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
import timeit
import traceback

from ..model.CPProcessor import CPProcessor
from ..model.CPLogging import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class ValidatorProcessor(CPProcessor):
    def __init__(self, instructions, config_files):
        super(ValidatorProcessor, self).__init__(instructions, "Validator")

        LOG.info('%s()' % KenLog.fcn())

        self._instructions = instructions
        self._config_files = config_files
        self._instructions['validator_success'] = {}

    def process(self):
        LOG.info('%s()' % KenLog.fcn())

        invoke_args = (self._instructions, self._config_files)

        order = self.get_plugin_order('validator', 'validators', invoke_args)
        for validator in order:
            mgr = self.load_plugin('validator', validator, invoke_args)
            if not mgr:
                continue

            if not mgr.driver.is_compatible_with_cloud(invoke_args):
                continue

            self._instructions['validator_success'][validator] = True

            if mgr.driver.check_dependency_success():
                self.start_plugin(validator)
                try:
                    duration = timeit.timeit(mgr.driver.validate, number=1)
                except Exception as e:
                    msg = 'Validator %s encountered an exception: %s\n' % (
                        validator, e)
                    self.log_and_print_error(KenLog.fcn(), msg
                                             + traceback.format_exc())
                    self._instructions['validator_success'][validator] = False
                    continue

                self.process_warnings(mgr, validator)

                if not self.process_errors(mgr, validator):
                    self._instructions['validator_success'][validator] = False
                    continue

                self.complete_plugin(validator, duration)
            else:
                msg = 'Validator %s skipped since a dependent validator failed' % validator
                self.log_and_print_message(KenLog.fcn(), msg)
                self._instructions['validator_success'][validator] = False
