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

from helion_configurationprocessor.cp.controller.CloudConfigProcess \
    import CloudConfigProcess
from helion_configurationprocessor.cp.model.ModelInitializerBase \
    import ModelInitializerBase
from helion_configurationprocessor.cp.model.JsonConfigFile \
    import JsonConfigFile
from helion_configurationprocessor.cp.model.YamlConfigFile \
    import YamlConfigFile


class model_1_0(ModelInitializerBase):
    def __init__(self, version, instructions, config_files, models,
                 cloud_path, site_path):
        super(model_1_0, self).__init__(version, instructions, config_files,
                                        models, cloud_path, site_path)

    def load_models(self):
        self._load_cloud_architecture()
        self.load_model('MachineArchitecture',
                        file_name='machine_architecture.json')
        self.load_model('EnvironmentConfig',
                        file_type='environment')
        self.load_model('NetworkConfig',
                        file_type='network-config')
        self.load_model('BaremetalConfig',
                        file_type='baremetal-config')
        self.load_model('ServerConfig',
                        file_type='server-config')
        self.load_model('NodeTypeConfig',
                        file_name='node_type.json')

        # CloudConfig is different because it has to collect a series
        # of input files, rather than the others that employ a
        # one-file-per-model
        p = CloudConfigProcess('CloudConfig', self._site_path,
                               self._cloud_path, self._instructions)
        if p.load(self._models['CloudDescription']):
            self._models['CloudConfig'] = p.model
        else:
            self.add_errors(p.errors)

    def _load_cloud_architecture(self):
        model = dict()

        self._load_ca(model, 'network_traffic', 'network-traffic', 'mnemonic')
        self._load_ca(model, 'services', 'service-components', 'name')
        self._load_ca(model, 'services', 'services', 'name')
        self._process_ca(model)

        self._models['CloudArchitecture'] = model

    def _load_ca_topic(self, model, file_name, topic, sort_key):
        if file_name.endswith('.json'):
            cf = JsonConfigFile(topic, file_name)
            cf.load()

        elif file_name.endswith('.yml') or file_name.endswith('.yaml'):
            cf = YamlConfigFile(topic, file_name)
            cf.load()

        else:
            return

        element = cf.contents

        if 'product' not in element:
            self.add_error('File "%s" is missing the section "product"' %
                           file_name)
            return

        if topic not in element:
            return

        for elem in element[topic]:
            self._add_element(model, topic, elem, sort_key)

    def _load_ca(self, model, file_base, topic, sort_key):
        for suffix in ['json', 'yml', 'yaml']:
            file_name = '%s.%s' % (file_base, suffix)
            s_path = os.path.join(self._site_path, file_name)
            if os.path.exists(s_path) and os.path.isfile(s_path):
                self._load_ca_topic(model, s_path, topic, sort_key)

        s_path = os.path.join(self._site_path, file_base)
        if os.path.exists(s_path) and os.path.isdir(s_path):
            for root, dirs, files in os.walk(s_path):
                for f in files:
                    file_name = os.path.join(root, f)
                    self._load_ca_topic(model, file_name, topic, sort_key)

    def _process_ca(self, model):
        for elem_sc in model['service-components']:
            if 'network-traffic' not in elem_sc:
                continue

            for elem_nt in elem_sc['network-traffic']:
                self._process_service_ca(model, elem_sc, elem_nt)

    def _process_service_ca(self, model, elem_sc, elem_nt):
        for cur_nt in model['network-traffic']:
            if cur_nt['mnemonic'] != elem_nt['traffic-group']:
                continue

            element = dict()
            element['service'] = elem_sc['mnemonic']
            element['ports'] = elem_nt['ports']

            if 'control-plane' in elem_nt:
                element['control-plane'] = elem_nt['control-plane']

            if 'service-connections' not in cur_nt:
                cur_nt['service-connections'] = []

            cur_nt['service-connections'].append(element)

    def _add_element(self, model, topic, element, sort_key):
        if topic not in model:
            model[topic] = []

        topic_model = model[topic]
        topic_model.append(element)
        topic_model = sorted(topic_model, key=lambda x: x[sort_key].lower())
        model[topic] = topic_model
