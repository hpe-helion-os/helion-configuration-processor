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

from copy import deepcopy

from helion_configurationprocessor.cp.model.CPLogging import \
    CPLogging as KenLog
from helion_configurationprocessor.cp.model.GeneratorPlugin \
    import GeneratorPlugin
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel
from helion_configurationprocessor.cp.model.v2_0.HlmVariable \
    import HlmVariable


LOG = logging.getLogger(__name__)


class ConsumesGenerator(GeneratorPlugin):
    def __init__(self, instructions, models, controllers):
        super(ConsumesGenerator, self).__init__(
            2.0, instructions, models, controllers,
            'consumes-generator-2.0')
        LOG.info('%s()' % KenLog.fcn())

    def generate(self):
        LOG.info('%s()' % KenLog.fcn())

        self._action = KenLog.fcn()
        cloud_internal = CloudModel.internal(self._models['CloudModel'])

        components = CloudModel.get(cloud_internal, 'components', [])
        # If we have an error in an earlier generator we may not have
        # components in the internal model
        if not components:
            return
        components_by_mnemonic = CloudModel.get(cloud_internal, 'components_by_mnemonic')
        control_planes = CloudModel.get(cloud_internal, 'control-planes')

        for cp_name, cp in control_planes.iteritems():
            for comp_name, comp_data in cp.get('components', []).iteritems():
                comp_data['consumes'] = self._get_consumes(comp_name,
                                                           components,
                                                           components_by_mnemonic,
                                                           cp)

    # Build the set of component consumes relationships in the context of a
    # specific control plane
    def _get_consumes(self, component_name, components, components_by_mnemonic, cp):

        result = {}

        component = components[component_name]
        for consume in component.get('consumes-services', []):
            consume_name = "consumes_%s" % consume['service-name'].replace('-', '_')
            result[consume_name] = {}
            consumes = result[consume_name]

            if 'relationship-vars' in consume:
                consumes['vars'] = {}
                for var in consume['relationship-vars']:
                    payload = var['properties'] if 'properties' in var else None
                    value = HlmVariable.generate_value(
                        self._instructions, self._models,
                        self._controllers, var['name'], var['value'],
                        payload=payload)
                    consumes['vars'][var['name']] = value

            consumed_component_name = components_by_mnemonic[consume['service-name']]['name']
            consumed_component = components[consumed_component_name]

            consumes['name'] = consumed_component_name

            ep = self._get_endpoint(consumed_component_name, cp)

            if not ep:
                # Some consumes relationships are optional.
                if consume.get('optional', False):
                    continue

                msg = ("%s expects to consume %s, but %s "
                       "doesn't have an internal endpoint." %
                       (component_name, consumed_component_name,
                        consumed_component_name))
                self.add_error(msg)
                continue

            for role, role_data in ep.iteritems():

                # Never give a public endpoint to a consumer
                if role == 'public':
                    continue

                # CP used 'private' as the name for  internal endpoints
                # in the playbooks so we have to stick with that
                if role == 'internal':
                    role_name = 'private'
                else:
                    role_name = role

                for data in role_data:
                    if 'address' in data.get('access', {}):

                        if ('consumes-vips' in consume
                                and role not in consume['consumes-vips']):
                            continue

                        if data['access']['use-tls']:
                            protocol = component.get('tls_protocol', 'https')
                        else:
                            protocol = component.get('nontls_protocol', 'http')
                        url = "%s://%s:%s" % (protocol,
                                              data['access']['hostname'],
                                              data['access']['port'])
                        if 'vips' not in consumes:
                            consumes['vips'] = {}
                        if role_name not in consumes['vips']:
                            consumes['vips'][role_name] = []

                        consumes['vips'][role_name].append({'ip_address': data['access']['address'],
                                                            'network': data['access']['network'],
                                                            'host': data['access']['hostname'],
                                                            'port': data['access']['port'],
                                                            'protocol': protocol,
                                                            'url': url,
                                                            'use_tls': data['access']['use-tls']})
                for data in role_data:
                    if 'members' in data.get('access', {}):

                        if ('consumes-members' in consume
                                and role not in consume['consumes-members']):
                            continue

                        if 'members' not in consumes:
                            consumes['members'] = {}
                        if 'role_name' not in consumes['members']:
                            consumes['members'][role_name] = []
                        for member in data['access']['members']:
                            consumes['members'][role_name].append({'host': member['hostname'],
                                                                   'ip_address': member['ip_address'],
                                                                   'network': member['network'],
                                                                   'port': data['access']['port'],
                                                                   'use_tls': data['access']['use-tls']})

            # TODO: Remove once all playbooks have switched to using
            #      internal vips insterad of public
            # Hack needed to keep compatiblity with 1.0  playbooks
            # which consumed public endpoints
            if consumed_component.get('publish-internal-as-public', False):
                if 'vips' in consumes and 'private' in consumes['vips']:
                    consumes['vips']['public'] = \
                        deepcopy(consumes['vips']['private'])
                if 'members' in consumes and 'private' in consumes['members']:
                    consumes['members']['public'] = \
                        deepcopy(consumes['members']['private'])

        return result

    def _get_endpoint(self, component_name, cp):
        #
        # Get the endpoint for a component from the control plane
        # or its parent
        #
        ep = cp['endpoints'].get(component_name, {})
        if not ep:
            if 'parent-cp' in cp:
                ep = self._get_endpoint(component_name, cp['parent-cp'])

        return ep

    def get_dependencies(self):
        return ['cloud-cplite-2.0']
