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
from helion_configurationprocessor.cp.model.Version import Version


class CloudModel(object):
    @staticmethod
    def version(cloud_model, version):
        v = Version.normalize(version)
        if v in cloud_model:
            return cloud_model[v]

        cloud_model[v] = dict()
        return cloud_model[v]

    @staticmethod
    def internal(cloud_model):
        if 'internal' in cloud_model:
            return cloud_model['internal']

        cloud_model['internal'] = dict()
        return cloud_model['internal']

    @staticmethod
    def get(cloud_element, key, default=None):
        if key in cloud_element:
            return cloud_element[key]
        # Note: Have to check for None as default could be an empty list
        elif default is not None:
            return default
        else:
            raise Exception("Missing data object %s" % key)

    @staticmethod
    def put(cloud_element, key, value):
        cloud_element[key] = value

    @staticmethod
    def get_version(cloud_model):
        return
