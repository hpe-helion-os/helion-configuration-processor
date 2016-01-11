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
import yaml
from yaml.constructor import ConstructorError

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from .ConfigFile import ConfigFile
from .ConfigFile import ConfigFileFormat


class OurYamlException(Exception):
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __str__(self):
        lines = []
        for exception in self.exceptions:
            lines.append(str(exception))
        return "\n".join(lines)


def no_duplicates_constructor(loader, node, deep=False):
    """Check for duplicate keys."""

    mapping = {}
    errors = []
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        value = loader.construct_object(value_node, deep=deep)
        if key in mapping:
            errors.append(ConstructorError("while constructing a mapping", node.start_mark,
                                           "found duplicate key (%s)" % key, key_node.start_mark))
        mapping[key] = value

    if len(errors) > 0:
        raise OurYamlException(errors)
    return loader.construct_mapping(node, deep)


def constructor(loader, node, deep=False):
    return loader.construct_mapping(node, deep)


class YamlConfigFile(ConfigFile):
    def __init__(self, name, path):
        super(YamlConfigFile, self).__init__(name, path, ConfigFileFormat.YAML)

    def __repr__(self, *args, **kwargs):
        return 'YamlConfigFile: name=%s, path=%s' % (self.name, self.path)

    def is_valid(self):
        """
        :return:
            True if the config file seems valid
            False if there are any format errors
        """
        if not self.is_loaded:
            return False

        if len(self.errors) > 0:
            return False

        return True

    def load(self, check_duplicates=True):
        try:
            fp = open(self.path, 'r')
        except OSError as e:
            msg = 'Cannot open file %s (%s)' % (self.path, e)
            self.add_error(msg)
            return

        if check_duplicates:
            yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                                 no_duplicates_constructor)
        else:
            yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                                 constructor)

        try:
            lines = fp.readlines()
            self._contents = yaml.load(''.join(lines))

        except (ConstructorError, OurYamlException) as e:
            msg = 'Found issues in file %s\n%s' % (self.path, e)
            self.add_warning(msg)
            self.load(check_duplicates=False)

        except (TypeError, ValueError) as e:
            msg = 'Cannot parse file %s\n%s' % (self.path, e)
            self.add_error(msg)
            return

        finally:
            fp.close()

        self.is_loaded = True
