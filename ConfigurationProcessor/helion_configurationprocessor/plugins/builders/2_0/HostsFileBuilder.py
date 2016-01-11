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
from operator \
    import itemgetter

import logging
import logging.config

from helion_configurationprocessor.cp.model.v2_0.HlmPaths \
    import HlmPaths
from helion_configurationprocessor.cp.model.v2_0.CloudDescription \
    import CloudDescription
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel

from helion_configurationprocessor.cp.model.BuilderPlugin \
    import BuilderPlugin
from helion_configurationprocessor.cp.model.BuilderPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class HostsFileBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(HostsFileBuilder, self).__init__(
            2.0, instructions, models, controllers,
            'hosts-file-2.0')
        LOG.info('%s()' % KenLog.fcn())

        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions, self.cloud_desc)
        self._file_path = os.path.join(self._file_path, 'net')

        self._cloud_model = self._models['CloudModel']
        self._cloud_version = CloudModel.version(self._cloud_model, self._version)
        self._cloud_internal = CloudModel.internal(self._cloud_model)

        HlmPaths.make_path(self._file_path)

    def build(self):
        LOG.info('%s()' % KenLog.fcn())

        file_name = os.path.join(self._file_path, 'hosts.hf')
        self.add_artifact(file_name, ArtifactMode.CREATED)

        allocated_addresses = CloudModel.get(self._cloud_internal, 'address_allocations')
        host_aliases = CloudModel.get(self._cloud_internal, 'host_aliases')
        cloud_name = CloudDescription.get_cloud_name(self.cloud_desc)

        with open(file_name, 'w') as fp:
            fp.write("# Cloud: %s\n" % (cloud_name))
            fp.write("\n")
            fp.write("# Localhost Information\n")
            fp.write("127.0.0.1      localhost\n")
            fp.write("\n")

            for group_name, group in allocated_addresses.iteritems():
                fp.write("#\n")
                fp.write("# Network Group: %s\n" % (group_name))
                fp.write("#\n")
                for network_name, network in group.iteritems():
                    fp.write("# Network: %s\n" % (network_name))
                    ips = []
                    for addr in network:
                        aliases = host_aliases.get(group_name,
                                                   {}).get(network_name,
                                                           {}).get(addr, [])
                        for name in aliases:
                            # Expand the address to a string with leading spaces
                            # in each quad so that it sorts by version
                            ips.append(["%3s.%3s.%3s.%3s" % tuple(addr.split(".")), name])
                    for ip in sorted(ips, key=itemgetter(0)):
                        fp.write("%-16s %s\n" % (ip[0].replace(" ", ""), ip[1]))

    def get_dependencies(self):
        return []
