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
import logging.config

from helion_configurationprocessor.cp.model.ControlPlane import ControlPlane
from helion_configurationprocessor.cp.model.Tier import Tier

from helion_configurationprocessor.cp.controller.CloudNameController \
    import CloudNameController

from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import ExplainerPlugin
from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import ordinal
from helion_configurationprocessor.cp.model.ExplainerPlugin \
    import pluralize
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class CloudStructureExplainer(ExplainerPlugin):
    def __init__(self, instructions, models, controllers):
        super(CloudStructureExplainer, self).__init__(
            1, instructions, models, controllers,
            'cloud-structure')
        LOG.info('%s()' % KenLog.fcn())

    def explain(self):
        LOG.info('%s()' % KenLog.fcn())

        fp = self._get_explainer_file()

        message = self._get_title()
        message += self._get_structure()

        fp.write('%s' % message)

        self._close_explainer_file(fp)

    def _get_title(self):
        message = '::Cloud Structure::\n\n'
        return message

    def _get_structure(self):
        nt_controller = self._controllers['NodeType']

        path = self._instructions['cloud_input_path']
        name, nickname = CloudNameController.get_cloud_names(path)

        if nickname and (len(nickname) > 0):
            message = 'The "%s" cloud was created with a nickname of "%s" ' % (
                name, nickname)
        else:
            message = 'The "%s" cloud was created with no nickname ' % name

        num_cp = len(self._models['CloudModel']['control-planes'])
        message += 'and "%d" defined control %s.\n\n' % \
                   (num_cp, pluralize(num_cp, 'plane', 'planes'))

        cp_index = 1
        for elem_cp in self._models['CloudModel']['control-planes']:
            if not ControlPlane.is_active(elem_cp):
                continue

            cp_type = ControlPlane.get_name(elem_cp)
            num_tiers = ControlPlane.get_active_tier_count(elem_cp)
            str_tiers = pluralize(num_tiers, 'tier', 'tiers')
            message += 'The %s control plane is a "%s" (%s) and has "%d" ' \
                       '%s.\n' % (ordinal(cp_index), cp_type, elem_cp['type'],
                                  num_tiers, str_tiers)

            t_index = 1
            for elem_t in elem_cp['tiers']:
                if not Tier.is_active(elem_t):
                    continue

                mc = Tier.get_active_member_count(elem_t)
                if mc == 1:
                    message += 'The %s tier in this control plane is not ' \
                               'clustered.' % ordinal(t_index)
                else:
                    message += 'The %s tier in this control plane is ' \
                               'clustered, having "%s" %s in the cluster.' % \
                               (ordinal(t_index), mc,
                                pluralize(mc, 'member', 'members'))
                message += '\n'

                t_index += 1

            if ('resource-nodes' not in elem_cp or
                    elem_cp['resource-nodes'] == {}):
                message += 'There are no resource nodes defined in this ' \
                           'control plane.\n'
            else:
                for rn, elem_rn in six.iteritems(elem_cp['resource-nodes']):
                    count = elem_rn['count']
                    node_type = nt_controller.get(rn)

                    fn_singular = node_type.friendly_name
                    fn_plural = node_type.friendly_name + 's'

                    message += 'There %s %s %s (%s) ' \
                               'defined in this control plane.\n' % (
                                   pluralize(count, 'is', 'are'), count,
                                   pluralize(count, fn_singular, fn_plural),
                                   rn)

            message += '\n'
            cp_index += 1

        return message

    def get_dependencies(self):
        return []
