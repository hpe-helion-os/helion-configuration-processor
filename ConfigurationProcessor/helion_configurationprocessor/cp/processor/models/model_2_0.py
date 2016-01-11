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
from helion_configurationprocessor.cp.model.ModelInitializerBase \
    import ModelInitializerBase


class model_2_0(ModelInitializerBase):
    def __init__(self, version, instructions, config_files, models,
                 cloud_path, site_path):
        super(model_2_0, self).__init__(version, instructions, config_files,
                                        models, cloud_path, site_path)

    def load_models(self):
        self.load_empty_model('CloudArchitecture', 'service-components')
        self.load_empty_model('CloudArchitecture', 'services')
        self.load_empty_model('MachineArchitecture', 'vendor')
        self.load_empty_model('EnvironmentConfig', 'node-type')
        self.load_empty_model('NetworkConfig', 'logical-interfaces')
        self.load_empty_model('ServerConfig', 'servers')
        self.load_empty_model('NodeTypeConfig', 'node-type')
        self.load_empty_model('CloudConfig', 'control-planes')
        self.load_model('BaremetalConfig',
                        file_type='baremetal-config')
        version = self.version()
        self.load_versioned_model(version, 'services')
        self.load_versioned_model(version, 'service-components')
        self.load_versioned_model(version, 'disk-models')
        self.load_versioned_model(version, 'availability_zones', optional=True)
        self.load_versioned_model(version, 'interface-models')
        self.load_versioned_model(version, 'servers')
        self.load_versioned_model(version, 'nic-mappings', optional=True)
        self.load_versioned_model(version, 'networks')
        self.load_versioned_model(version, 'control-planes', alias='regions')
        self.load_versioned_model(version, 'server-roles')
        self.load_versioned_model(version, 'server-groups', optional=True)
        self.load_versioned_model(version, 'network-groups')
        self.load_versioned_model(version, 'ring-specifications', optional=True)
        self.load_versioned_model(version, 'pass-through', optional=True)
        self.load_versioned_model(version, 'firewall-rules', optional=True)
