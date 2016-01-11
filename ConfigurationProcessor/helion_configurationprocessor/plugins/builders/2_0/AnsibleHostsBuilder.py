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
import logging
import logging.config

from helion_configurationprocessor.cp.model.v2_0.HlmPaths \
    import HlmPaths
from helion_configurationprocessor.cp.model.v2_0.CloudDescription \
    import CloudDescription
from helion_configurationprocessor.cp.model.v2_0.CloudModel \
    import CloudModel
from helion_configurationprocessor.cp.model.v2_0 \
    import ServerState

from helion_configurationprocessor.cp.model.BuilderPlugin \
    import BuilderPlugin
from helion_configurationprocessor.cp.model.BuilderPlugin \
    import ArtifactMode
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog


LOG = logging.getLogger(__name__)


class AnsibleHostsBuilder(BuilderPlugin):
    def __init__(self, instructions, models, controllers):
        super(AnsibleHostsBuilder, self).__init__(
            2.0, instructions, models, controllers,
            'ansible-hosts-2.0')
        LOG.info('%s()' % KenLog.fcn())
        self.cloud_desc = self._models['CloudDescription']['cloud']
        self._file_path = HlmPaths.get_output_path(self._instructions, self.cloud_desc)
        self._file_path = os.path.join(self._file_path, 'ansible')

        self._cloud_model = self._models['CloudModel']
        self._cloud_version = CloudModel.version(self._cloud_model, self._version)
        self._cloud_internal = CloudModel.internal(self._cloud_model)

        HlmPaths.make_path(self._file_path)

    def build(self):
        LOG.info('%s()' % KenLog.fcn())

        cloud_name = CloudDescription.get_cloud_name(self.cloud_desc)
        control_planes = CloudModel.get(self._cloud_internal, 'control-planes')
        components = CloudModel.get(self._cloud_internal, 'components')
        server_groups = CloudModel.get(self._cloud_internal, 'server-groups')

        filename = "%s/hosts/localhost" % (self._file_path)
        self.add_artifact(filename, ArtifactMode.CREATED)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        with open(filename, 'w') as f:
            f.write("localhost\n")

        filename = "%s/hosts/verb_hosts" % (self._file_path)
        self.add_artifact(filename, ArtifactMode.CREATED)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        with open(filename, 'w') as f:
            f.write("[localhost]\n")
            f.write("localhost\n")
            f.write("\n")

            f.write("[resources:children]\n")
            for cp_name in sorted(control_planes):
                cp = control_planes[cp_name]
                for cluster in cp['clusters']:
                    for server in cluster['servers']:
                        f.write("%s\n" % server['hostname'])
                for resource_group_name, resource_group in cp.get('resources', {}).iteritems():
                    for server in resource_group['servers']:
                        f.write("%s\n" % server['hostname'])
            f.write("\n")

            # Build a list of all control_planes
            f.write("[%s:children]\n" % (cloud_name))
            for cp_name in sorted(control_planes):
                f.write("%s-%s\n" % (cloud_name, cp_name))
            f.write("\n")

            # List all clusters and resource in a control plane
            for cp_name in sorted(control_planes):
                cp = control_planes[cp_name]
                f.write("[%s-%s:children]\n" % (cloud_name, cp_name))
                for cluster in cp['clusters']:
                    f.write("%s-%s-%s\n" % (cloud_name, cp_name, cluster['name']))
                for resource_group_name in cp.get('resources', []):
                    f.write("%s-%s-%s\n" % (cloud_name, cp_name, resource_group_name))
                f.write("\n")

            # List all members of each clusters in a cp
            for cp_name in sorted(control_planes):
                cp = control_planes[cp_name]
                for cluster in cp['clusters']:
                    f.write("[%s-%s-%s:children]\n" % (cloud_name, cp_name, cluster['name']))
                    for server in cluster['servers']:
                        f.write("%s\n" % server['hostname'])
                    f.write("\n")

                    for server in cluster['servers']:
                        f.write("[%s]\n" % server['hostname'])
                        f.write("%s ansible_ssh_host=%s\n" % (server['hostname'], server['addr']))
                        f.write("\n")

                for resource_group_name, resource_group in cp.get('resources', {}).iteritems():
                    f.write("[%s-%s-%s:children]\n" % (cloud_name, cp_name, resource_group_name))
                    for server in resource_group['servers']:
                        f.write("%s\n" % server['hostname'])
                    f.write("\n")

                    for server in resource_group['servers']:
                        f.write("[%s]\n" % server['hostname'])
                        f.write("%s ansible_ssh_host=%s\n" % (server['hostname'], server['addr']))
                        f.write("\n")

            # Build list of hosts by component accross all cps
            component_list = {}
            for cp_name, cp in control_planes.iteritems():
                for component_name, component_data in cp['components'].iteritems():
                    if component_name not in components:
                        print "Warning: No data for %s when building host_vars" % component_name
                        continue

                    component_mnemonic = components[component_name]['mnemonic']

                    if component_mnemonic not in component_list:
                        component_list[component_mnemonic] = {}

                    if cp_name not in component_list[component_mnemonic]:
                        component_list[component_mnemonic][cp_name] = {}

                    for cluster in cp['clusters']:
                        if (component_name in cluster['service-components'] or
                                component_name in cp.get('common-service-components', [])):

                            if cluster['name'] not in component_list[component_mnemonic][cp_name]:
                                component_list[component_mnemonic][cp_name][cluster['name']] = []
                            host_list = component_list[component_mnemonic][cp_name][cluster['name']]

                            for server in cluster['servers']:
                                host_list.append(server['hostname'])

                    if 'resources' in cp:
                        for r_name, resources in cp['resources'].iteritems():
                            if (component_name in resources['service-components'] or
                                    component_name in cp.get('common-service-components', [])):

                                if r_name not in component_list[component_mnemonic][cp_name]:
                                    component_list[component_mnemonic][cp_name][r_name] = []
                                host_list = component_list[component_mnemonic][cp_name][r_name]

                                for server in resources['servers']:
                                    host_list.append(server['hostname'])

            for component_name in sorted(component_list):
                component_data = component_list[component_name]
                f.write("[%s:children]\n" % (component_name))
                for cp_name in sorted(component_data):
                    f.write("%s-%s\n" % (component_name, cp_name))
                f.write("\n")

                for cp_name in sorted(component_data):
                    f.write("[%s-%s:children]\n" % (component_name, cp_name))
                    cluster_data = component_data[cp_name]
                    for cluster in sorted(cluster_data):
                        f.write("%s-%s-%s\n" % (component_name, cp_name, cluster))
                    f.write("\n")

                    for cluster in sorted(cluster_data):
                        f.write("[%s-%s-%s:children]\n" % (component_name, cp_name, cluster))
                        hosts = cluster_data[cluster]
                        for host in sorted(hosts):
                            f.write("%s\n" % host)
                        f.write("\n")

            # Build list of server groups
            for sg_name, sg in server_groups.iteritems():
                f.write("[%s:children]\n" % (sg_name))
                for child in sg.get('server-groups', []):
                    f.write("%s\n" % child)
                for server in sg.get('servers', []):
                    if server['state'] == ServerState.ALLOCATED:
                        f.write("%s\n" % server['hostname'])
                f.write("\n")

    def get_dependencies(self):
        return []
