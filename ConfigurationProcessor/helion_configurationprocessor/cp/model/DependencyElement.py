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


class DependencyElement(object):
    def __init__(self, plugin):
        self._plugin = plugin
        self._dependencies = plugin.get_dependencies()

    @property
    def slug(self):
        return self._plugin.slug

    @property
    def plugin(self):
        return self._plugin

    @property
    def dependencies(self):
        return self._dependencies

    def remove_dependency(self, slug):
        if slug in self._dependencies:
            self._dependencies.remove(slug)

    def has_dependencies(self):
        return len(self._dependencies) > 0

    def has_dependency(self, slug):
        return slug in self._dependencies
