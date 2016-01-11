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
import os
import six

from abc import ABCMeta
from abc import abstractmethod

from .CPLogging import CPLogging as KenLog
from .CPVariables import CHECKPOINT_DIRECTORY
from .PluginBase import PluginBase

LOG = logging.getLogger(__name__)


class ArtifactMode(object):
    CREATED = 0
    MODIFIED = 1
    DELETED = 2
    COPIED = 3


@six.add_metaclass(ABCMeta)
class CheckpointerPlugin(PluginBase):
    def __init__(self, version, instructions, models, controllers, slug):
        super(CheckpointerPlugin, self).__init__(version, instructions, slug)

        LOG.info('%s()' % KenLog.fcn())

        self._models = models
        self._controllers = controllers
        self._artifacts = []
        self._path = None

    @abstractmethod
    def checkpoint(self):
        """ Take the model and checkpoint it.
        :return: True if the deploy succeeded, False if it failed.  Note
        that if it fails, the plugin should throw an exception.
        """
        pass

    def get_model_version(self):
        """ When a builder is executed, it needs to be compatible with the
        k-CP version that's being executed.  This will help us figure that out
        :return:
        """
        return '%03d' % self._version

    def get_checkpoint_path(self):
        return self._path

    def prepare_filesystem(self, cloud_name, subdir):
        cp_base = self._instructions['checkpoint_base']

        self._path = CHECKPOINT_DIRECTORY.replace('%CLOUD_NAME%', cloud_name)
        self._path = os.path.join(self._path, cp_base)
        self._path = os.path.join(self._path, subdir)

        if not os.path.exists(self._path):
            os.makedirs(self._path)
            self.add_artifact(self._path, ArtifactMode.CREATED)

    def get_artifacts(self):
        """ The builder is responsible for keeping track of the artifacts
        that it generates.  This would include paths to created or modified
        files. Created files should be prepended with (+), removed files
        should be prepended with (-), and modified files should be prepended
        with (*).
        :return: The list of artifacts
        """
        return self._artifacts

    def add_artifact(self, artifact, mode):

        a = '(?) '
        if mode == ArtifactMode.CREATED:
            a = '(+) '

        if mode == ArtifactMode.MODIFIED:
            a = '(*) '

        if mode == ArtifactMode.DELETED:
            a = '(-) '

        if mode == ArtifactMode.COPIED:
            a = '(>) '

        a += artifact

        self._artifacts.append(a)

    @property
    def models(self):
        return self._models

    @property
    def controllers(self):
        return self._controllers
