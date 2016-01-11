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
import logging.config

from helion_configurationprocessor.cp.model.CPLogging import \
    CPLogging as KenLog
from ..CloudConfigValidator import CloudConfigValidator as \
    CloudConfigValidator1_0


LOG = logging.getLogger(__name__)


class CloudConfigValidator(CloudConfigValidator1_0):
    def __init__(self, instructions, config_files):
        super(CloudConfigValidator1_0, self).__init__(
            2.0, instructions, config_files,
            'cloudconfig-2.0')
        LOG.info('%s()' % KenLog.fcn())
        self._is_built = False

    def _validate_cloud(self, model, return_value):
        LOG.info('%s()' % KenLog.fcn())

        return return_value
