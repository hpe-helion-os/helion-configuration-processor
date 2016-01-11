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

from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog
from ..ServersExplainer import ServersExplainer as \
    ServersExplainer1_0

LOG = logging.getLogger(__name__)


class ServersExplainer(ServersExplainer1_0):
    def __init__(self, instructions, models, controllers):
        super(ServersExplainer1_0, self).__init__(
            2.0, instructions, models, controllers,
            'servers-2.0')
        LOG.info('%s()' % KenLog.fcn())

    def explain(self):
        LOG.info('%s()' % KenLog.fcn())

        fp = self._get_explainer_file()

        self._close_explainer_file(fp)
