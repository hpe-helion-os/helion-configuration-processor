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
import os
import logging
import fnmatch
import six
import traceback

from ..model.CPProcessor import CPProcessor
from ..model.CPConfigFile import CPConfigFile
from ..model.CPLogging import CPLogging as KenLog
from ..model.Version import Version

LOG = logging.getLogger(__name__)


class InputProcessor(CPProcessor):
    def __init__(self, instructions):
        super(InputProcessor, self).__init__(instructions, "Input")

        LOG.info('%s()' % KenLog.fcn())

        self.instructions = instructions

        self._site_path = instructions['site_input_path']

        self._cloud_path = os.path.dirname(
            instructions['cloud_input_path'])

        # handle being pointed directly at the services directory
        # or the parent directory
        if os.path.basename(instructions['site_input_path']) == 'services':
            self._cloud_service_path = os.path.dirname(
                instructions['site_input_path'])
        else:
            self._cloud_service_path = instructions['site_input_path']

        self._cloud_service_dir = os.path.join(self._cloud_service_path,
                                               'services')

        self._config_files = []

    def process(self):
        LOG.info('%s()' % KenLog.fcn())
        self._errors = []
        try:
            self._load_inputs(self._cloud_path,
                              exclude=['services', 'service-components'])
            self._load_inputs(self._cloud_service_dir)
        except Exception as e:
            msg = 'InputProcessor encountered an exception: %s\n' % e
            self.log_and_print_error(KenLog.fcn(), msg
                                     + traceback.format_exc())
            self.add_error(e)

        return len(self._errors) == 0

    def is_required_for_cloud(self, input_version):
        return float(input_version) >= float(2)

    def version(self):
        return Version.get(self.instructions['cloud_input_path'])

    def _load_inputs(self, path, exclude=[]):
        LOG.info('%s()' % KenLog.fcn())
        exclude = [a.lower() for a in exclude]
        for filename in self._walk_dir(path):
            try:
                file_contents = self._load_file(filename, exclude=exclude)
            except Exception as e:
                self.add_error("Error loading %s: %s" % (filename, e))

            if file_contents == 'no-content':
                self.add_warning('file %s did not parse' % filename)
                continue
            if not file_contents:
                continue
            if len(self._config_files) == 0:
                self._config_files.append(file_contents)
            else:
                self._add_file_contents(file_contents)

    def _add_file_contents(self, file_contents):
        LOG.info('%s()' % KenLog.fcn())
        for version in self._config_files:
            if float(version['version']) == float(file_contents['version']):
                for key, value in six.iteritems(file_contents):
                    if key.lower() != 'version':
                        if key.lower() not in version:
                            if not isinstance(value, list):
                                version[key.lower()] = [value]
                            else:
                                version[key.lower()] = value
                        elif key.lower() in version:
                            version[key.lower()].extend(value)
                return
        self._config_files.append(file_contents)

    def _load_file(self, filename, exclude=[]):
        LOG.info('%s()' % KenLog.fcn())
        file_contents = CPConfigFile.parse(filename)
        file_warnings = CPConfigFile.warnings(filename)
        file_errors = CPConfigFile.errors(filename)
        if file_warnings:
            self._warnings += file_warnings
        if file_errors:
            self._errors += file_errors
            return 'no-content'
        element = dict()
        for key, value in six.iteritems(file_contents):
            if key.lower() in exclude:
                return None
            if key.lower() == 'product':
                element['version'] = float(value['version'])
            else:
                if not isinstance(value, list):
                    element[key] = [value]
                else:
                    element[key] = value
        return element

    def _create_content(self, version, key, value):
        LOG.info('%s()' % KenLog.fcn())
        content = dict()
        content['product'] = dict()
        content['product']['version'] = version
        content[key] = value

        return content

    def _walk_dir(self, path):
        LOG.info('%s()' % KenLog.fcn())
        for root, dirs, files in os.walk(path):
            for basename in files:
                if fnmatch.fnmatch(basename, '*.json'):
                    filename = os.path.join(root, basename)
                    if 'cloudConfig' not in filename:
                        yield filename
                if fnmatch.fnmatch(basename, '*.yml'):
                    filename = os.path.join(root, basename)
                    if 'cloudConfig' not in filename:
                        yield filename

    @property
    def config_files(self):
        return self._config_files
