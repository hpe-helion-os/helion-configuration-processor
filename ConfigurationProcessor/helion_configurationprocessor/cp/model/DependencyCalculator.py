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
from .DependencyElement import DependencyElement


class DependencyCalculator(object):
    def __init__(self, plugins):
        self._plugins = []
        for elem_p in plugins:
            de = DependencyElement(elem_p)
            self._plugins.append(de)

        self._ordered_plugins = []
        self._errors = []

    def __repr__(self):
        return 'DependencyCalculator: %s' % self.to_string()

    def calculate(self):
        while len(self._plugins) > 0:
            np = self._process()
            if np == 0 and len(self._plugins) > 0:
                if self._circular():
                    self._ordered_plugins = []
                    break

    def get(self):
        return [op.slug for op in self._ordered_plugins]

    def _circular(self):
        is_circular = False

        for elem_p1 in self._plugins:
            for elem_p2 in self._plugins:
                if elem_p1 == elem_p2:
                    continue

                if (elem_p1.has_dependency(elem_p2.slug) and
                        elem_p2.has_dependency(elem_p1.slug)):
                    error1 = 'Circular dependency detected: %s and %s are ' \
                             'both dependent upon each other' % (
                                 elem_p1.slug, elem_p2.slug)
                    error2 = 'Circular dependency detected: %s and %s are ' \
                             'both dependent upon each other' % (
                                 elem_p2.slug, elem_p1.slug)

                    if (error1 not in self._errors and
                            error2 not in self._errors):
                        self._errors.append(error1)

                    is_circular = True

        return is_circular

    @property
    def ok(self):
        return len(self._errors) == 0

    @property
    def errors(self):
        return self._errors

    def to_string(self):
        rv = ''

        for elem_op in self._ordered_plugins:
            rv += '%s, ' % elem_op.slug

        return rv

    def _process(self):
        for elem_p in self._plugins:
            if not elem_p.has_dependencies():
                self._plugins.remove(elem_p)
                self._ordered_plugins.append(elem_p)
                self._remove_dependency(elem_p)
                return 1

        return 0

    def _remove_dependency(self, plugin):
        for elem_op in self._plugins:
            if elem_op == plugin:
                continue

            elem_op.remove_dependency(plugin.slug)
