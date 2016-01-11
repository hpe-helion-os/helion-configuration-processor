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

from helion_configurationprocessor.cp.model.ValidatorPlugin \
    import ValidatorPlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog

from helion_configurationprocessor.cp.model.v2_0 \
    import AllocationPolicy


LOG = logging.getLogger(__name__)


class ControlPlanesValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(ControlPlanesValidator, self).__init__(
            2.0, instructions, config_files,
            'control-planes-2.0')
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())
        version = float(self.version())

        input = self._create_content(version, "control-planes")
        if input:
            result = self.validate_schema(input, "control-plane")
        else:
            # control planes used to be called regions
            input = self._create_content(version, "regions")
            result = self.validate_schema(input, "region")

        for cp in input['control-planes']:
            names = set()
            r_prefix = set()
            for cluster in cp.get('clusters', []):
                if cluster['name'] in names:
                    msg = ("Duplicate cluster/resource name: %s "
                           "in control plane %s" %
                           (cluster['name'], cp['name']))
                    self.add_error(msg)
                else:
                    names.add(cluster['name'])

                if 'allocation-policy' in cluster:
                    policy = cluster['allocation-policy']
                    if policy not in AllocationPolicy.valid:
                        msg = ("Invalid allocation policy %s "
                               "in cluster %s:%s" %
                               (policy, cp['name'], cluster['name']))
                        self.add_error(msg)

            if 'resource-nodes' in cp:
                msg = ("Control Plane '%s': Use of 'resource-nodes' is deprecated, "
                       "Use 'resources' instead." % (cp['name']))
                self.add_warning(msg)
                resources = cp['resource-nodes']
            else:
                resources = cp.get('resources', [])

            for resource in resources:
                if resource['name'] in names:
                    msg = ("Duplicate cluster/resource name: %s "
                           "in control plane %s" %
                           (resource['name'], cp['name']))
                    self.add_error(msg)
                else:
                    names.add(resource['name'])

                if 'resource-prefix' in resource:
                    if resource['resource-prefix'] in r_prefix:
                        msg = ("Duplicate resource-prefix: %s "
                               "in control plane %s" %
                               (resource['resource-prefix'], cp['name']))
                        self.add_error(msg)
                    else:
                        r_prefix.add(resource['resource-prefix'])

                if 'allocation-policy' in resource:
                    policy = resource['allocation-policy']
                    if policy not in AllocationPolicy.valid:
                        msg = ("Invalid allocation policy %s "
                               "in resource group %s:%s" %
                               (policy, cp['name'], resource['name']))
                        self.add_error(msg)

        LOG.info('%s()' % KenLog.fcn())
        return result

    @property
    def instructions(self):
        return self._instructions

    def get_dependencies(self):
        return []
