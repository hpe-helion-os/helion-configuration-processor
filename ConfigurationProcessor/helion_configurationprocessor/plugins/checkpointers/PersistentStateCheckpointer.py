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
import logging.config

from helion_configurationprocessor.cp.controller.CloudNameController \
    import CloudNameController

from helion_configurationprocessor.cp.model.CheckpointerPlugin \
    import CheckpointerPlugin
from helion_configurationprocessor.cp.model.CheckpointerPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class PersistentStateCheckpointer(CheckpointerPlugin):
    def __init__(self, instructions, models, controllers):
        super(PersistentStateCheckpointer, self).__init__(
            1, instructions, models, controllers,
            'persistent-state')
        LOG.info('%s()' % KenLog.fcn())

    def checkpoint(self):
        LOG.info('%s()' % KenLog.fcn())

        path = self._instructions['cloud_input_path']
        cloud_name, nickname = CloudNameController.get_cloud_names(path)
        self.prepare_filesystem(cloud_name, 'persistent_state')

        return self._checkpoint()

    def _checkpoint(self):
        src = self._get_from()
        dst = self._get_to()

        for o in os.listdir(src):
            src_obj = os.path.join(src, o)
            dst_obj = os.path.join(dst, o)

            self.add_artifact(dst_obj, ArtifactMode.COPIED)

            if os.path.isdir(src_obj):
                try:
                    shutil.copytree(src_obj, dst_obj)
                except Exception as e:
                    self.add_error('Could not copy dir "%s" to "%s": %s' % (
                        src_obj, dst_obj, e))

            else:
                try:
                    shutil.copy(src_obj, dst_obj)
                except Exception as e:
                    self.add_error('Could not copy file "%s" to "%s": %s' % (
                        src_obj, dst_obj, e))

        return self.ok

    def _get_from(self):
        cc_controller = self._controllers['CloudConfig']
        stage = cc_controller.get_output_path(self._models)

        ps = os.path.dirname(stage)
        ps = os.path.join(ps, 'persistent_state')

        return ps

    def _get_to(self):
        return self.get_checkpoint_path()

    def get_dependencies(self):
        return ['config']
