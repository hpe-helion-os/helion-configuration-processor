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

from .ConfigFileFormat import ConfigFileFormat


@six.add_metaclass(ABCMeta)
class ConfigFile(object):
    def __init__(self, file_name, file_path, req_elements=None,
                 data_fmt=ConfigFileFormat.UNKNOWN):
        self._name = file_name
        self._path = file_path
        self._data_format = data_fmt
        self._is_loaded = False
        self._contents = None
        self._errors = []
        self._warnings = []

    def __repr__(self, *args, **kwargs):
        return 'ConfigFile: name=%s, path=%s, data_format=%s, ' \
               'is_loaded=%s, errors=%s' % (
                   self._name,
                   self._path,
                   self._data_format,
                   self._is_loaded,
                   self._errors)

    @abstractmethod
    def is_valid(self):
        return False

    @abstractmethod
    def load(self):
        pass

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def data_format(self):
        return self._data_format

    @property
    def is_loaded(self):
        return self._is_loaded

    @is_loaded.setter
    def is_loaded(self, value):
        self._is_loaded = value

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, value):
        self._contents = value

    @property
    def errors(self):
        return self._errors

    @property
    def warnings(self):
        return self._warnings

    def add_error(self, error):
        self._errors.append(error)

    def add_warning(self, warning):
        self._warnings.append(warning)
