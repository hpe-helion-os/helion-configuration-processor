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


class InterfaceModelsValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(InterfaceModelsValidator, self).__init__(
            2.0, instructions, config_files,
            'interface-models-2.0')
        self._valid = False
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())

        version = float(self.version())

        input = self._create_content(version, "interface-models")
        self._valid = self.validate_schema(input, "interface_model")
        if self._valid:
            interface_models = input['interface-models']
            for model in interface_models:
                self._validate_devices_only_used_once(model)
            self._validate_names(interface_models)
            self._validate_bond_options(interface_models)

        return self._valid

    def _validate_names(self, interface_models):
        names = set()
        for model in interface_models:
            if model['name'] in names:
                msg = ("Interface model %s is defined more than once." %
                       (model['name']))
                self.add_error(msg)
                self._valid = False
            else:
                names.add(model['name'])

    def _validate_devices_only_used_once(self, interface_model):
        used_devices = set()
        for iface in interface_model['network-interfaces']:
            devices = [iface['device']['name']]
            if 'bond-data' in iface:
                devices.extend([dev['name'] for dev in iface['bond-data']['devices']])
            for device in devices:
                if device not in used_devices:
                    used_devices.add(device)
                else:
                    msg = ("Network interface '%s' in '%s': device '%s' is "
                           "already used. A device can only be used once per "
                           "interface model." %
                           (iface['name'], interface_model['name'], device))
                    self.add_error(msg)
                    self._valid = False

    def _validate_bond_options(self, interface_models):
        for interface_model in interface_models:
            for iface in interface_model['network-interfaces']:
                if 'bond-data' in iface:
                    self._check_deprecated_bond_options(iface, interface_model['name'])
                    self._validate_bond_mode(iface)
                    self._validate_bond_primary(iface, interface_model['name'])

    def _check_deprecated_bond_options(self, interface, interface_model_name):
        bond_options = interface['bond-data']['options']
        for option in bond_options.keys():
            if option.startswith('bond-'):
                msg = ("Network interface '%s' in '%s' uses the deprecated "
                       "bond option name '%s'. Please switch to using the name "
                       "'%s' instead." %
                       (interface['name'], interface_model_name, option,
                        option.replace('bond-', '')))
                self.add_warning(msg)

    def _validate_bond_mode(self, interface):
        valid_bond_modes = ['balance-rr', 0,
                            'active-backup', 1,
                            'balance-xor', 2,
                            'broadcast', 3,
                            '802.3ad', 4,
                            'balance-tlb', 5,
                            'balance-alb', 6]

        bond_options = interface['bond-data']['options']
        bond_mode = bond_options.get('mode', bond_options.get('bond-mode', None))
        if bond_mode is None:
            msg = ("Network interface '%s' is a bond but has not specified "
                   "'mode' as one of its options." % (interface['name']))
            self.add_error(msg)
            self._valid = False
            return
        if bond_mode not in valid_bond_modes:
            msg = ("Network interface %s: the chosen bond-mode "
                   "'%s' is invalid. Please choose a valid "
                   "bond-mode: %s" %
                   (interface['name'], bond_mode, valid_bond_modes))
            self.add_error(msg)
            self._valid = False

    def _validate_bond_primary(self, interface, interface_model_name):
        bond_primary_device = interface['bond-data']['options'].get('primary', None)
        bond_devices = [dev['name'] for dev in interface['bond-data']['devices']]
        if bond_primary_device and bond_primary_device not in bond_devices:
            msg = ("Network interface '%s' in '%s' specifies the bond-primary: "
                   "'%s', which does not appear in the bond's set of devices: %s" %
                   (interface['name'], interface_model_name, bond_primary_device,
                    bond_devices))
            self.add_error(msg)
            self._valid = False

    @property
    def instructions(self):
        return self._instructions

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, is_valid):
        self._valid = is_valid

    def get_dependencies(self):
        return []
