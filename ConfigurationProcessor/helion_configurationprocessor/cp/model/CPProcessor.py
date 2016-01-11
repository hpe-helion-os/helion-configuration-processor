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

from stevedore import driver

from .CPLogging import CPLogging as KenLog
from ..model.DependencyCalculator import DependencyCalculator


LOG = logging.getLogger(__name__)


@six.add_metaclass(ABCMeta)
class CPProcessor(object):
    def __init__(self, instructions, processor_type):
        LOG.info('%s()' % KenLog.fcn())

        self._instructions = instructions
        self._processor_type = processor_type

        self._errors = []
        self._warnings = []

    @abstractmethod
    def process(self):
        """ This is called to perform the process, kinda like the command
        pattern.

        :return: True if success, False if failure
        """
        pass

    def start_plugin(self, plugin_name):
        msg = '%s %s Started' % (self._processor_type, plugin_name)
        self.log_and_print_message(KenLog.fcn(), msg)

    def complete_plugin(self, plugin_name, duration):
        msg = '%s %s Completed in %0.3fs' % (
            self._processor_type, plugin_name, duration)
        self.log_and_print_message(KenLog.fcn(), msg)

    def load_plugin(self, namespace, plugin_name, invoke_args):
        try:
            mgr = driver.DriverManager(
                namespace='helion.configurationprocessor.%s' % namespace,
                name=plugin_name, invoke_on_load=True,
                invoke_args=invoke_args)
        except RuntimeError as e:
            msg = '%s %s Failed to load: %s' % (
                self._processor_type, plugin_name, e)
            self.log_and_print_error(KenLog.fcn(), msg)
            return None
        except Exception as e:
            msg = '%s %s Failed to load: %s' % (
                self._processor_type, plugin_name, e)
            self.log_and_print_error(KenLog.fcn(), msg)
            return None

        return mgr

    def validate_plugin_version(self, mgr, _):
        return (int(mgr.driver.get_model_version()) !=
                int(self._instructions['model_version']))

    def get_plugin_order(self, plugin_type_s, plugin_type_p, invoke_args):
        plugins = []

        for p in self._instructions[plugin_type_p]:
            mgr = self.load_plugin(plugin_type_s, p, invoke_args)
            if not mgr:
                continue

            plugins.append(mgr.driver)

        calculator = DependencyCalculator(plugins)
        calculator.calculate()

        if not calculator.ok:
            self.add_errors(calculator.errors)

        return calculator.get()

    def _build_line(self, plugin_name, output_type, output_text):
        line = '#   %s' % plugin_name
        while len(line) < 30:
            line += ' '

        line += '%s: %s' % (output_type, output_text)
        return line

    def process_warnings(self, mgr, plugin_name):
        if len(mgr.driver.warnings) > 0:
            msg = ''

            for w in mgr.driver.warnings:
                line = self._build_line(plugin_name, 'WRN', w)
                msg += line

                if w != mgr.driver.warnings[-1]:
                    msg += '\n'

            self.log_and_add_warning(KenLog.fcn(), msg)

    def process_errors(self, mgr, plugin_name):
        if not mgr.driver.ok:
            msg = ''

            for e in mgr.driver.errors:
                line = self._build_line(plugin_name, 'ERR', e)
                msg += line

                if e != mgr.driver.errors[-1]:
                    msg += '\n'

            self.log_and_add_error(KenLog.fcn(), msg)

            return False

        return True

    def process_artifacts(self, mgr, plugin_name):
        artifacts = mgr.driver.get_artifacts()
        if artifacts:
            msg = '%s %s Generated the following artifacts:\n' \
                  % (self._processor_type, plugin_name)
            for a in artifacts:
                msg += '\t%s' % a

                if a != artifacts[-1]:
                    msg += '\n'
        else:
            msg = '%s %s Generated no artifacts' % (
                self._processor_type, plugin_name)

        self.log_and_print_message(KenLog.fcn(), msg)

    def log_and_print_message(self, fcn, msg):
        LOG.debug('%s(): %s' % (fcn, msg))
        print('%s' % msg)

    def log_and_print_error(self, fcn, msg):
        LOG.error('%s(): %s' % (fcn, msg))
        self.add_error(msg)
        print('%s' % msg)

    def log_and_add_error(self, fcn, msg):
        LOG.error('%s(): %s' % (fcn, msg))
        self.add_error(msg)

    def log_and_print_warning(self, fcn, msg):
        LOG.warning('%s(): %s' % (fcn, msg))
        self.add_warning(msg)
        print('%s' % msg)

    def log_and_add_warning(self, fcn, msg):
        LOG.warning('%s(): %s' % (fcn, msg))
        self.add_warning(msg)

    @property
    def ok(self):
        return len(self._errors) == 0

    @property
    def errors(self):
        return self._errors

    def add_error(self, error):
        self._errors.append(error)

    def add_errors(self, errors):
        for error in errors:
            self._errors.append(error)

    @property
    def warnings(self):
        return self._warnings

    def add_warning(self, warning):
        self._warnings.append(warning)

    def add_warnings(self, warnings):
        for warning in warnings:
            self._warnings.append(warning)
