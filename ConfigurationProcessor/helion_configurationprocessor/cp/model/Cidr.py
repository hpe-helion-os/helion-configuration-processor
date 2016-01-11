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

from netaddr import IPNetwork

from .CPLogging import CPLogging as KenLog
from .StatePersistor import StatePersistor


LOG = logging.getLogger(__name__)


class Cidr(object):
    def __init__(self, cidr, models=None, controllers=None):
        LOG.info('%s(): cidr="%s"' % (KenLog.fcn(), cidr))

        self._cidr = cidr
        self._models = models
        self._controllers = controllers

        self._ip = IPNetwork(cidr)
        self._start_address = self.get_first_address()
        self._ip_size = self._ip.size

        self._ip_index_start = 1
        self._ip_index_end = 1
        self._update_from_cache()

        self._gateway = None

    def get_first_address(self):
        for ip in self._ip.iter_hosts():
            return ip

    def get_next_address(self):
        LOG.info('%s()' % KenLog.fcn())

        value = self._ip[self._ip_index_end]
        self._ip_index_end += 1

        self._set_cache()

        LOG.debug('get_next_address(): value=%s, ip_index_end=%s' % (
            value, self._ip_index_end))

        return value.format()

    def _set_cache(self):
        if not self._models or not self._controllers:
            return

        cache = StatePersistor(
            self._models, self._controllers, persistence_file='cidr.yml')

        elem = dict()
        elem['ip_index_start'] = self._ip_index_start
        elem['ip_index_end'] = self._ip_index_end

        cache_info = dict()
        cache_info[self._cidr] = elem

        cache.persist_info(cache_info)

    def _get_cache(self):
        if not self._models or not self._controllers:
            return

        cache = StatePersistor(
            self._models, self._controllers, persistence_file='cidr.yml')

        cached_info = cache.recall_info([self._cidr])
        return cached_info

    def _update_from_cache(self):
        cache = self._get_cache()
        if cache:
            if self._ip_index_start < cache['ip_index_start']:
                self._ip_index_start = cache['ip_index_start']

            if self._ip_index_end < cache['ip_index_end']:
                self._ip_index_end = cache['ip_index_end']

    @property
    def netmask(self):
        return self._ip.netmask

    @property
    def gateway(self):
        return self._gateway

    @gateway.setter
    def gateway(self, value):
        self._gateway = value

    def to_json(self):
        value = '{ '
        value += '"cidr": "%s", ' % self._cidr
        value += '"start-address": "%s", ' % str(self._ip)
        value += '"ip-index-start": %d, ' % self._ip_index_start
        value += '"ip-index-end": %d' % self._ip_index_end

        if self._gateway:
            value += ', "gateway": "%s"' % self._gateway

        value += ' }'

        return value

    @property
    def cidr(self):
        return self._cidr

    @property
    def start_address(self):
        return self._start_address

    @start_address.setter
    def start_address(self, value):
        self._ip_index_start = 1
        self._ip_index_end = 1
        self._start_address = value

        test_address = IPNetwork(value).ip

        for ip in self._ip.iter_hosts():
            if hex(ip) == hex(test_address):
                break

            self._ip_index_start += 1
            self._ip_index_end += 1

        self._update_from_cache()

    @property
    def ip_size(self):
        return self._ip_size

    @property
    def ip_index_start(self):
        return self._ip_index_start

    @ip_index_start.setter
    def ip_index_start(self, value):
        self._ip_index_start = value

    @property
    def ip_index_end(self):
        return self._ip_index_end

    @ip_index_end.setter
    def ip_index_end(self, value):
        self._ip_index_end = value
