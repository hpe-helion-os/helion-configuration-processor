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

from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import ExplainerPlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class OverrideVarsExplainer(ExplainerPlugin):
    def __init__(self, instructions, models, controllers):
        super(OverrideVarsExplainer, self).__init__(
            1, instructions, models, controllers,
            'override-vars')
        LOG.info('%s()' % KenLog.fcn())

    def explain(self):
        LOG.info('%s()' % KenLog.fcn())

        fp = self._get_explainer_file()

        message = self._get_title()
        message += self._get_overrides()

        fp.write('%s' % message)

        self._close_explainer_file(fp)

    def _get_title(self):
        message = '::Override Variables::\n\n'
        return message

    def _get_overrides(self):
        cloud_model = self._models['CloudModel']

        if 'journal' not in cloud_model:
            message = 'There is no journal available in the cloud model.\n'
            return message

        journal = cloud_model['journal']
        if 'override-vars' not in journal:
            message = 'There were no variables overridden during this run ' \
                      'of the configuration processor\n'
            return message

        message = 'The following variable overrides were encountered: \n'

        for elem_ov in journal['override-vars']:
            message += '\t%s\n' % elem_ov

        return message

    def get_dependencies(self):
        return ['cloud-structure',
                'network-traffic-groups',
                'servers',
                'services']
