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
import sys
import time
import timeit
import logging
import logging.config
import traceback

from .ModelProcessor import ModelProcessor
from .ControllerProcessor import ControllerProcessor
from .ValidatorProcessor import ValidatorProcessor
from .MigratorProcessor import MigratorProcessor
from .GeneratorProcessor import GeneratorProcessor
from .BuilderProcessor import BuilderProcessor
from .ExplainerProcessor import ExplainerProcessor
from .CheckpointerProcessor import CheckpointerProcessor
from .FinalizerProcessor import FinalizerProcessor
from .InputProcessor import InputProcessor
from .CleanUpStageProcessor import CleanUpStageProcessor

from ..model.Version import Version

from ..model.CPLogging import CPLogging as KenLog

LOG = logging.getLogger(__name__)


class ConfigurationProcessor(KenLog):
    def __init__(self, instructions):
        super(ConfigurationProcessor, self).__init__(instructions)

        self._instructions = instructions
        self._models = None
        self._controllers = None
        self._config_files = None

        self._errors = []
        self._warnings = []

        self._banner = '#' * 50

        dashes = '-' * 20
        LOG.info('\n%s Process Started at %s %s' % (dashes, time.strftime(
            "%c"), dashes))

        LOG.info('%s()' % KenLog.fcn())

        self._establish_version()

    def _establish_version(self):
        LOG.info('%s()' % KenLog.fcn())

        try:
            version = Version.get(self._instructions['cloud_input_path'])
            version = Version.normalize(version)
            self._instructions['model_version'] = version

            self._establish_path('cloud_output_path', version)
            self._establish_path('network_output_path', version)
            self._establish_path('persistent_state', version)
            self._establish_path('cloud_checkpoint_path', version)
        except Exception as e:
            msg = 'Configuration Processor encountered an exception: %s\n' % e
            LOG.error(msg + traceback.format_exc())
            sys.stderr.write(traceback.format_exc())
            exit(int(-1))

        print('@@@ Processing cloud model version %s' % version)

    def _establish_path(self, element, version):
        val = self._instructions[element]
        val = val.replace('@CLOUD_VERSION@', version)
        self._instructions[element] = val

    def process_input(self):
        LOG.error('%s()' % KenLog.fcn())
        print("\n%s Input Processing Started %s" % (
            self._banner, self._banner))

        processor = InputProcessor(self._instructions)

        if not processor.is_required_for_cloud(processor.version()):
            print('\nInput processing not needed - skipping')
            return True

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            self._config_files = processor.config_files
            print('\nInput Processing Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Validate Process Started %s" % (
            self._banner, self._banner))

        processor = ValidatorProcessor(self._instructions, self._config_files)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            print('\nValidate Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def create_models(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Model Creation Process Started %s" % (
            self._banner, self._banner))

        processor = ModelProcessor(self._instructions, self._config_files)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            self._models = processor.models
            print('\nModel Creation Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def create_controllers(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Controller Creation Process Started %s" % (
            self._banner, self._banner))

        processor = ControllerProcessor(
            self._instructions, self._models)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            self._controllers = processor.controllers
            print('\nController Creation Process Succeeded in %0.3fs' %
                  duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def migrate(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Migration Process Started %s" % (
            self._banner, self._banner))

        processor = MigratorProcessor(
            self._instructions, self._models, self._controllers)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            self._models = processor.models

            print('\nMigration Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def clean_up_stage(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s CleanUpStage Process Started %s" % (
            self._banner, self._banner))

        processor = CleanUpStageProcessor(self._instructions, self._models)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            print('\nCleanUpStage Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def generate(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Generate Process Started %s" % (
            self._banner, self._banner))

        processor = GeneratorProcessor(
            self._instructions, self._models, self._controllers)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            print('\nGenerate Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def build(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Build Process Started %s" % (
            self._banner, self._banner))

        processor = BuilderProcessor(
            self._instructions, self._models, self._controllers)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            print('\nBuild Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def explain(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Explanation Process Started %s" % (
            self._banner, self._banner))

        processor = ExplainerProcessor(
            self._instructions, self._models, self._controllers)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            print('\nExplanation Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def checkpoint(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Checkpoint Process Started %s" % (
            self._banner, self._banner))

        processor = CheckpointerProcessor(
            self._instructions, self._models, self._controllers)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            print('\nCheckpoint Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    def finalize(self):
        LOG.info('%s()' % KenLog.fcn())
        print("\n%s Finalize Process Started %s" % (
            self._banner, self._banner))

        processor = FinalizerProcessor(
            self._instructions, self._models, self._controllers,
            self._config_files)

        try:
            duration = timeit.timeit(processor.process, number=1)
            self.add_warnings(processor.warnings)
            if not processor.ok:
                self.add_errors(processor.errors)
                return False

            print('\nFinalize Process Succeeded in %0.3fs' % duration)
            return True

        except Exception as e:
            print('Unknown Exception: %s' % e)
            return False

    @property
    def errors(self):
        return self._errors

    def add_error(self, error):
        self._errors.append(error)

    def add_errors(self, errors):
        for error in errors:
            self._errors.append(error)

    def _print_errors(self, action):
        LOG.error(action)
        for error in self.errors:
            LOG.error('\t\t%s' % error)

    @property
    def warnings(self):
        return self._warnings

    def add_warning(self, warning):
        self._warnings.append(warning)

    def add_warnings(self, warnings):
        for warning in warnings:
            self._warnings.append(warning)

    def _print_warnings(self, action):
        LOG.warning(action)
        for warning in self.warnings:
            LOG.warning('\t\t%s' % warning)


def exit(exit_code):
    LOG.info('Process terminated with return code %d' % exit_code)
    sys.exit(exit_code)
