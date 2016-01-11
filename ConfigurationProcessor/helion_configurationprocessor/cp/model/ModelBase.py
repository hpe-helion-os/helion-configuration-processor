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
from abc import ABCMeta
from abc import abstractmethod

import six


@six.add_metaclass(ABCMeta)
class ModelBase(object):
    def __init__(self, instructions):
        self._instructions = instructions

    @abstractmethod
    def to_json(self):
        pass

    def stringify(self, num_spaces, index, value):
        return '%s"%s": "%s"' % (' ' * num_spaces, index, value)
