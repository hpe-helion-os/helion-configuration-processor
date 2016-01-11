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


LOG = logging.getLogger(__name__)


class NicMappingsValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(NicMappingsValidator, self).__init__(
            2.0, instructions, config_files,
            'nic-mappings-2.0')
        self._valid = False
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())

        version = float(self.version())

        input = self._create_content(version, "nic-mappings")
        # Nic mappings are optional
        if not input:
            return True

        self._valid = self.validate_schema(input, "nic_mapping")
        if self._valid:
            nic_mappings = input['nic-mappings']
            self._validate_names(nic_mappings)
            for mapping in nic_mappings:
                self._validate_logical_names_and_addresses(mapping)

        LOG.info('%s()' % KenLog.fcn())
        return self._valid

    def _validate_names(self, nic_mappings):
        #
        # Check each mapping is only defined once
        #
        names = set()
        for mapping in nic_mappings:
            if mapping['name'] in names:
                msg = ("NIC mapping  %s is defined more than once" %
                       (mapping['name']))
                self.add_error(msg)
                self._valid = False
            else:
                names.add(mapping['name'])

    def _validate_logical_names_and_addresses(self, nic_mapping):
        #
        # Check each mapping is only defined once
        #
        logical_names = set()
        addresses = {}
        for port in nic_mapping.get('physical-ports', []):
            if port['logical-name'] in logical_names:
                msg = ("Logical name '%s' is defined more than once "
                       "in nic mapping '%s'" %
                       (port['logical-name'], nic_mapping['name']))
                self.add_error(msg)
                self._valid = False
            else:
                logical_names.add(port['logical-name'])

            addr = port.get('bus-address')
            port_attr = port.get('port-attributes', {})
            port_num = port_attr.get('port-num')

            if not addr:
                msg = ("Missing Bus Address in NIC mapping\n"
                       "    nic_mapping: '%s' "
                       "logical-name: '%s' - bus-address missing" %
                       (nic_mapping['name'], port['logical-name']))
                self.add_error(msg)
                self._valid = False
                continue

            if addr in addresses and addresses[addr]['type'] != port['type']:
                msg = ("Multiple type for same Bus Address in NIC mapping\n"
                       "    nic_mapping: '%s' "
                       "bus-address '%s' defined as both '%s' and '%s' " %
                       (nic_mapping['name'], addr, addresses[addr]['type'], port['type']))
                self.add_error(msg)
                self._valid = False
                continue

            if port['type'] == 'simple-port':
                if addr in addresses:
                    msg = ("Duplicate Bus Address in NIC mapping\n"
                           "    nic_mapping: '%s' "
                           "logical-name: '%s' - bus-address '%s' previously defined as type 'simple-port'" %
                           (nic_mapping['name'], port['logical-name'], addr))
                    self.add_error(msg)
                    self._valid = False
                    continue

                elif port_num is not None:
                    msg = ("Invalid Port number in NIC mapping\n"
                           "    nic_mapping: '%s' "
                           "logical-name: '%s' - port-num not supported for type 'simple-port'" %
                           (nic_mapping['name'], port['logical-name']))
                    self.add_error(msg)
                    self._valid = False
                    continue

            elif port['type'] == 'multi-port':
                if port_num is None:
                    msg = ("Missing Port number in NIC mapping\n"
                           "    nic_mapping: '%s' "
                           "logical-name: '%s' - port-num required in port-attributes for type 'multi-port'" %
                           (nic_mapping['name'], port['logical-name']))
                    self.add_error(msg)
                    self._valid = False
                    continue

                if port_num in addresses.get(addr, {}).get('ports', []):
                    msg = ("Duplicate Port number in NIC mapping\n"
                           "    nic_mapping: '%s' "
                           "logical-name: '%s' bus address '%s' - port-num '%s' previously defined" %
                           (nic_mapping['name'], port['logical-name'], addr, port_num))
                    self.add_error(msg)
                    self._valid = False
                    continue

            if addr not in addresses:
                addresses[addr] = {'type': port['type'],
                                   'ports': []}

            if port['type'] == 'multi-port':
                addresses[addr]['ports'].append(port_num)

    @property
    def instructions(self):
        return self._instructions

    def get_dependencies(self):
        return []
