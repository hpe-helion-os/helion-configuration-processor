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
from .JsonConfigFile import JsonConfigFile
from .YamlConfigFile import YamlConfigFile


class CPConfigFile(object):
    @staticmethod
    def parse(filename):
        if isinstance(filename, dict):
            return filename

        if filename.endswith('.json'):
            return CPConfigFile.parse_json(filename)

        if filename.endswith('.yml') or filename.endswith('.yaml'):
            return CPConfigFile.parse_yaml(filename)

        return None

    @staticmethod
    def parse_json(filename):
        json_config = JsonConfigFile('json_file', filename)
        json_config.load()
        if json_config.is_valid():
            return json_config.contents

        return None

    @staticmethod
    def parse_yaml(filename):
        yaml_config = YamlConfigFile('yaml_file', filename)
        yaml_config.load()
        if yaml_config.is_valid():
            return yaml_config.contents

        return None

    @staticmethod
    def errors(filename):
        if filename.endswith('.json'):
            return CPConfigFile.get_json_errors(filename)

        if filename.endswith('.yml') or filename.endswith('.yaml'):
            return CPConfigFile.get_yaml_errors(filename)

        return None

    @staticmethod
    def warnings(filename):
        if filename.endswith('.json'):
            # Not implemented
            return None

        if filename.endswith('.yml') or filename.endswith('.yaml'):
            return CPConfigFile.get_yaml_warnings(filename)

    @staticmethod
    def get_json_errors(filename):
        json_config = JsonConfigFile('json_file', filename)
        json_config.load()
        if json_config.is_valid():
            return None

        return json_config.errors

    @staticmethod
    def get_yaml_errors(filename):
        yaml_config = YamlConfigFile('yaml_file', filename)
        yaml_config.load()
        if yaml_config.is_valid():
            return None

        return yaml_config.errors

    @staticmethod
    def get_yaml_warnings(filename):
        yaml_config = YamlConfigFile('yaml_file', filename)
        yaml_config.load()
        return yaml_config.warnings

    @staticmethod
    def get_full_input_path(cloud_input_path, filename):
        dir_name = os.path.dirname(cloud_input_path)
        if filename[0] != os.path.sep:
            return os.path.join(dir_name, filename)
        else:
            return filename
