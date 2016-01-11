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
import shutil
import logging
import traceback

from ..model.CPProcessor import CPProcessor
from ..model.CPLogging import CPLogging as KenLog
from ..model.Version import Version
from ..model.v2_0.HlmPaths import HlmPaths

LOG = logging.getLogger(__name__)


class CleanUpStageProcessor(CPProcessor):
    def __init__(self, instructions, models):
        super(CleanUpStageProcessor, self).__init__(instructions, "CleanUpStage")

        LOG.info('%s()' % KenLog.fcn())

        self._instructions = instructions
        self._models = models

        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions, self.cloud_desc)

    def process(self):
        LOG.info('%s()' % KenLog.fcn())
        self._errors = []
        try:
            if os.path.isdir(self._file_path):
                for name in os.listdir(self._file_path):
                    path = "%s/%s" % (self._file_path, name)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)

        except Exception as e:
            msg = 'CleanUpStageProcessor encountered an exception: %s\n' % e
            self.log_and_print_error(KenLog.fcn(), msg
                                     + traceback.format_exc())
            self.add_error(e)

        return len(self._errors) == 0

    def is_required_for_cloud(self, input_version):
        return float(input_version) >= float(2)

    def version(self):
        return Version.get(self.instructions['cloud_input_path'])
