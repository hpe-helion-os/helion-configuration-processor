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
import simplejson as json

from .ConfigFile import ConfigFile
from .ConfigFile import ConfigFileFormat


class JsonConfigFile(ConfigFile):
    def __init__(self, name, path):
        super(JsonConfigFile, self).__init__(name, path, ConfigFileFormat.JSON)

    def __repr__(self, *args, **kwargs):
        return 'JsonConfigFile: name=%s, path=%s' % (self.name, self.path)

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

    def load(self):
        try:
            fp = open(self.path, 'r')
        except (OSError, IOError) as e:
            msg = 'Cannot open file %s (%s)' % (self.path, e)
            self.add_error(msg)
            return

        try:
            self._contents = json.load(fp)
        except (TypeError, ValueError) as e:
            msg = 'Cannot parse file %s: %s' % (self.path, e)
            self.add_error(msg)
            return

        finally:
            fp.close()

        self.is_loaded = True
