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
import logging

from copy import deepcopy
from ..model.CPLogging import CPLogging as KenLog

LOG = logging.getLogger(__name__)


class DataTransformer(object):
    def __init__(self, data):
        LOG.info('%s()' % KenLog.fcn())
        self._data = deepcopy(data)

    def all_output(self, from_token='-', to_token='_'):
        LOG.info('%s()' % KenLog.fcn())
        if isinstance(self._data, list):
            result = self.list_output(self._data, from_token, to_token)
        elif isinstance(self._data, dict):
            result = self.dict_output(self._data, from_token, to_token)
        else:
            result = self._data

        return result

    def list_output(self, data, from_token, to_token):
        LOG.info('%s()' % KenLog.fcn())
        for item in data:
            if isinstance(item, list):
                item = self.list_output(item, from_token, to_token)
            elif isinstance(item, dict):
                item = self.dict_output(item, from_token, to_token)

        return data

    def dict_output(self, data, from_token, to_token):
        LOG.info('%s()' % KenLog.fcn())
        for key, value in data.iteritems():
            if isinstance(key, str):
                newkey = key.replace(from_token, to_token)
                data[newkey] = data.pop(key)

            if isinstance(value, list):
                value = self.list_output(value, from_token, to_token)
            elif isinstance(value, dict):
                value = self.dict_output(value, from_token, to_token)
        return data
