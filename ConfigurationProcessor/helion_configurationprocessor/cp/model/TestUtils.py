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


class TestUtils(object):
    @staticmethod
    def validate_attributes(obj, attributes, available_attributes,
                            private_methods=[]):
        for a in attributes:
            if a.startswith('_') and not a.startswith('__') and not \
                    a.startswith('_abc_'):
                if a not in available_attributes and a not in private_methods:
                    obj.assertEqual(a, '<--- UNKNOWN_ATTRIBUTE')

    @staticmethod
    def validate_public_methods(obj, methods, available_methods):
        for m in methods:
            if not m.startswith('_'):
                if m not in available_methods:
                    obj.assertEqual(m, '<--- UNKNOWN_METHOD')

    @staticmethod
    def validate_enum(obj, values, available_values, ignore_list=[]):
        for v in values:
            if not v.startswith('_'):
                if v not in available_values and v not in ignore_list:
                    obj.assertEqual(v, '<--- UNKNOWN_VALUE')

    @staticmethod
    def build_full_cloud_model():
        cloud_model = dict()
        cloud_model['failure-zones'] = TestUtils.build_failure_zones()

        return cloud_model

    @staticmethod
    def build_failure_zones():
        failure_zones = []

        fz1 = dict()
        fz1['name'] = 'fz1'
        failure_zones.append(fz1)

        fz2 = dict()
        fz2['name'] = 'fz2'
        failure_zones.append(fz2)

        fz3 = dict()
        fz3['name'] = 'fz3'
        failure_zones.append(fz3)

        return failure_zones
