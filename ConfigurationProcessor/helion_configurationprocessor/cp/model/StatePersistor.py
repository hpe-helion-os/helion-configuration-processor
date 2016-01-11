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
import yaml
import os


class StatePersistor():
    def __init__(self, models, controllers,
                 persistence_file='general.yml',
                 persistence_path=None):

        if persistence_path:
            self._persistence_path = persistence_path
        else:
            cloud_config = controllers['CloudConfig']
            self._persistence_path = cloud_config.get_persistent_path(models)

        self.persistence_file = self._persistence_path + persistence_file

        if not os.path.isdir(self._persistence_path):
            os.makedirs(self._persistence_path)

        if (os.path.isfile(self.persistence_file) and
                os.stat(self.persistence_file).st_size != 0):
            self._data_dict = yaml.load(open(self.persistence_file))
        else:
            self._data_dict = dict()

    def persist_info(self, info_dict):
        self._data_dict.update(info_dict)

        with open(self.persistence_file, 'w') as yaml_file:
            yaml.safe_dump(self._data_dict, yaml_file,
                           allow_unicode=False, default_flow_style=False)

    def delete_info(self, keys):
        for key in keys:
            if key in self._data_dict:
                del self._data_dict[key]

        with open(self.persistence_file, 'w') as yaml_file:
            yaml.safe_dump(self._data_dict, yaml_file,
                           allow_unicode=False, default_flow_style=False)

    def recall_info(self, lookup_array=None):
        if not self._data_dict:
            return dict()

        if not lookup_array:
            return self._data_dict

        current_dict = self._data_dict
        for key in lookup_array:
            current_dict = current_dict.get(key)

        return current_dict
