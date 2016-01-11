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


class CloudDescription(object):
    @staticmethod
    def get_version(cloud_description):
        return cloud_description['product']['version']

    @staticmethod
    def get_server_config(instructions, cloud_description):
        path = os.path.dirname(instructions['cloud_input_path'])
        path = os.path.join(path, cloud_description['cloud']['server-config'])
        return path
