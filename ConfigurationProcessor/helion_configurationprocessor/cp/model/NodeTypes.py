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


class NodeTypes(object):
    @staticmethod
    def get(model, type_name):
        for elem_nt in model:
            if NodeTypes.equals(elem_nt, type_name):
                return elem_nt

        return None

    @staticmethod
    def equals(elem_nt, type_name):
        if type_name.find('-') != -1:
            tokens = type_name.split('-')
            name = tokens[0]
        else:
            name = type_name

        return elem_nt['type-name'].lower() == name.lower()

    @staticmethod
    def get_elements(elem_nt):
        tokens = elem_nt.split('-')
        i = len(tokens) - 1
        while i >= 0:
            try:
                int(tokens[i])
                i -= 1
            except Exception:
                break

        name = tokens[0]
        j = 1
        while j < i:
            name += '-%s' % tokens[j]
            j += 1

        version = tokens[i + 1] if (i + 1) < len(tokens) else None
        model_class = tokens[i + 2] if (i + 2) < len(tokens) else None

        return name, version, model_class

    @staticmethod
    def get_name(elem_nt):
        type_name, _, _ = NodeTypes.get_elements(elem_nt)
        return type_name

    @staticmethod
    def get_version(elem_nt):
        _, version, _ = NodeTypes.get_elements(elem_nt)
        return version

    @staticmethod
    def get_model_class(elem_nt):
        _, _, model_class = NodeTypes.get_elements(elem_nt)
        return model_class
