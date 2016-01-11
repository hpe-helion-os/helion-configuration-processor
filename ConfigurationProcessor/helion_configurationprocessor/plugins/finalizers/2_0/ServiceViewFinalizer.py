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

import logging
import logging.config
import yaml

from helion_configurationprocessor.cp.model.v2_0.HlmPaths \
    import HlmPaths
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel

from helion_configurationprocessor.cp.model.FinalizerPlugin \
    import FinalizerPlugin
from helion_configurationprocessor.cp.model.FinalizerPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class ServiceViewFinalizer(FinalizerPlugin):
    def __init__(self, instructions, models, controllers, config_files):
        super(ServiceViewFinalizer, self).__init__(
            2.0, instructions, models, controllers, config_files,
            'service-view-2.0')
        LOG.info('%s()' % KenLog.fcn())

        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions,
                                                   self.cloud_desc)
        self._file_path = os.path.join(self._file_path, 'info')

        self._cloud_model = self._models['CloudModel']
        self._cloud_version = CloudModel.version(self._cloud_model,
                                                 self._version)
        self._cloud_internal = CloudModel.internal(self._cloud_model)

        HlmPaths.make_path(self._file_path)

    def finalize(self):
        LOG.info('%s()' % KenLog.fcn())

        service_view = CloudModel.get(self._cloud_internal, 'service_view', {})

        filename = os.path.join(self._file_path, 'service_info.yml')
        self.add_artifact(filename, ArtifactMode.CREATED)

        with open(filename, 'w') as fp:
            yaml.dump(service_view.get('by_region', {}), fp, default_flow_style=False, indent=4)

    def get_dependencies(self):
        return []
