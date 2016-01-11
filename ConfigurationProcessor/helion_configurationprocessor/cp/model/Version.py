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
from ..model.CPVariables import MODEL_VERSION
from ..model.JsonConfigFile import JsonConfigFile
from ..model.YamlConfigFile import YamlConfigFile


class Version(object):
    @staticmethod
    def get(file_name):
        if file_name.endswith('.json'):
            cf = JsonConfigFile('cloudConfig', file_name)
            cf.load()

        elif file_name.endswith('.yml') or file_name.endswith('.yaml'):
            cf = YamlConfigFile('cloudConfig', file_name)
            cf.load()

        else:
            return MODEL_VERSION

        element = cf.contents

        elem_p = element.get('product', dict())
        elem_v = elem_p.get('version', MODEL_VERSION)

        return elem_v

    @staticmethod
    def validate(file_name, model):
        cloud_version = Version.get(file_name)

        elem_p = model.get('product', dict())
        version = elem_p.get('version', MODEL_VERSION)

        try:
            return int(cloud_version) == int(version)

        except Exception:
            return False

    @staticmethod
    def normalize(version):
        return '%.1f' % float(version)

    @staticmethod
    def normalize_to_underscore(version):
        v = Version.normalize(version)
        return v.replace('.', '_')
