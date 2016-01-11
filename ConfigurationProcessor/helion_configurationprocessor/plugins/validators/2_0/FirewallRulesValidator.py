# (c) Copyright 2015 Hewlett Packard Enterprise Development Company #
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import logging
import logging.config

from helion_configurationprocessor.cp.model.ValidatorPlugin \
    import ValidatorPlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog

from netaddr import IPNetwork, IPAddress

LOG = logging.getLogger(__name__)


class FirewallRulesValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(FirewallRulesValidator, self).__init__(
            2.0, instructions, config_files,
            'firewall-rules-2.0')
        self._valid = False
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())

        version = float(self.version())

        input = self._create_content(version, 'firewall-rules')
        if input:
            self._valid = self.validate_schema(input, 'firewall_rules')
            if self._valid:
                fw_rules = input.get('firewall-rules', [])
                for fw_rule in fw_rules:
                    self._validate_remote_ip_prefix(fw_rule)
            return self._valid
        else:
            return True

    def _validate_remote_ip_prefix(self, fw_rule):
        for rule in fw_rule.get('rules', []):
            if 'remote-ip-prefix' in rule:
                remote_ip_prefix = rule['remote-ip-prefix']
                try:
                    IPNetwork(remote_ip_prefix)
                except Exception:
                    try:
                        IPAddress(remote_ip_prefix)
                    except Exception:
                        msg = ("Firewall rule '%s': '%s' is not a valid IP address "
                               "or prefix." % (fw_rule['name'], remote_ip_prefix))
                        self.add_error(msg)
                        self._valid = False

    @property
    def instructions(self):
        return self._instructions

    def get_dependencies(self):
        return []
