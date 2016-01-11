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
import six
import logging
import yaml
import pprint

from jsonschema import SchemaError
from jsonschema import _utils
from jsonschema import validators
from jsonschema import Draft4Validator
from collections import deque

from abc import ABCMeta
from abc import abstractmethod

from .CPConfigFile import CPConfigFile
from .CPLogging import CPLogging as KenLog
from .PluginBase import PluginBase
from Version import Version

LOG = logging.getLogger(__name__)


class ArtifactMode(object):
    CREATED = 0
    MODIFIED = 1
    DELETED = 2
    COPIED = 3


@six.add_metaclass(ABCMeta)
class ValidatorPlugin(PluginBase):
    def __init__(self, version, instructions, config_files, slug):
        super(ValidatorPlugin, self).__init__(version, instructions, slug)

        LOG.info('%s()' % KenLog.fcn())

        self._is_valid_anywhere = ['_comment']
        self._config_files = config_files

    @property
    def is_valid_anywhere(self):
        return self._is_valid_anywhere

    @abstractmethod
    def validate(self):
        """ Take the model and construct some output according to the
        instructions
        :return: True if the validation succeeded, False if it failed.  Note
        that if it fails, the plugin should throw an exception.
        """
        pass

    def version(self):
        return Version.get(self.instructions['cloud_input_path'])

    def get_path(self, path, file_type):
        cloud_config = os.path.basename(self._instructions['cloud_input_path'])
        file_name = os.path.join(path, cloud_config)

        file_contents = CPConfigFile.parse(file_name)
        if not file_contents:
            return None

        return file_contents['cloud'].get(file_type, None)

    def get_full_path(self, path, file_type):
        cloud_config = os.path.basename(self._instructions['cloud_input_path'])
        file_name = os.path.join(path, cloud_config)

        file_contents = CPConfigFile.parse(file_name)
        if not file_contents:
            return None

        return os.path.join(path, file_contents['cloud'][file_type])

    def get_schema_path(self, file_base):
        path_name = self._instructions['cloud_schema_path']
        path_name = os.path.join(path_name, 'Schema')
        path_name = os.path.join(path_name, str(self._version))
        path_name = os.path.join(path_name, file_base)

        suffixes = ['.json', '.yml', '.yaml']
        for s in suffixes:
            schema_name = path_name + s
            if os.path.exists(schema_name):
                return schema_name

        return None

    def get_path_contents(self, path):
        return CPConfigFile.parse(path)

    def get_path_errors(self, path):
        return CPConfigFile.errors(path)

    def validate_exists(self, path, filename):
        if not filename:
            return False

        if filename.startswith(os.path.sep):
            self._path = filename
        else:
            self._path = '%s/%s' % (path, filename)

        if not os.path.exists(self._path):
            self.add_error('Could not locate "%s" in "%s"' % (filename, path))
            return False

        return True

    def validate_schema_exists(self, file_base):
        schema_path = self.get_schema_path(file_base)
        if not schema_path:
            self.add_error('Could not locate the schema for "%s"' % file_base)
            return False

        return True

    def validate_parsing(self):
        try:
            model = CPConfigFile.parse(self._path)

        except Exception as e:
            if str(e).find('Expecting property name:') != -1:
                self.add_error(str(e) +
                               ' -- Check for an unnecessary comma on the '
                               'previous line')
            else:
                msg = 'File "%s" encountered a parsing error: %s' % (
                    self._path, e)
                self.add_error(msg)

            return None

        return model

    def validate_schema(self, data_file, file_base):
        return_value = True

        schema_file = self.get_schema_path(file_base)

        try:
            schema_contents = CPConfigFile.parse(schema_file)
            data_contents = CPConfigFile.parse(data_file)
            # We've already checked the input files for errors, but not the
            # schema files
            schema_errors = CPConfigFile.errors(schema_file)
            schema_warnings = CPConfigFile.warnings(schema_file)
            if schema_warnings:
                self._warnings += schema_warnings
            if schema_errors:
                self._errors += schema_errors
                return False
        except Exception as e:
            msg = ('Syntax errors detected, data:"%s" schema "%s" errors "%s" '
                   % (data_file, schema_file, e))
            self.add_error(msg)
            return_value = False

        try:
            schema_check = validators.validator_for(schema_contents)
            schema_check.check_schema(schema_contents)
        except SchemaError as e:
            self.add_error('Schema "%s" is invalid: %s' % (
                schema_contents, e))
            return False

        try:
            validate = Draft4Validator(schema_contents)
            error_list = [err for err in validate.iter_errors(data_contents)]
            if len(error_list) > 0:
                error_string = '\n\nInput\n%s\n\nCould not be validated - list of errors:\n' % (
                    _utils.indent(yaml.dump(data_contents, default_flow_style=False, indent=4)))
                for e in error_list:
                    error_string += "%s\n%s\n%s\n" % (
                        _utils.indent("Index of error:       %s" %
                                      _utils.format_as_index(deque(e.path))),
                        _utils.indent("    Erroneous value:     %s" %
                                      pprint.pformat(e.instance, width=72)),
                        _utils.indent("    Expected type:       %s" %
                                      e.validator_value))
                self.add_error(error_string)
                return_value = False

        except Exception as e:
            self.add_error('File "%s" or "%s" could not be loaded: %s' % (
                schema_file, data_file, e))
            return_value = False

        return return_value

    # This just gives validate_parsing another name
    def load(self):
        return self.validate_parsing()

    def check_dependency_success(self):
        for dependency in self.get_dependencies():
            if not self._instructions['validator_success'][dependency]:
                return False
        return True

    def _validate_product(self, model, return_value):
        LOG.info('%s()' % KenLog.fcn())

        req_elems = ['version']
        opt_elems = []
        return_value = self._validate_section(
            model, req_elems, opt_elems,
            self._path, 'Top-Level', return_value)

        LOG.debug('%s() -> %s' % (KenLog.fcn(), return_value))
        return return_value

    def _validate_section(self, model, req_elems, opt_elems, file_name,
                          cur_elem, return_value):
        LOG.info('%s(): file_name="%s", cur_elem="%s"' % (
            KenLog.fcn(), file_name, cur_elem))

        for elem in req_elems:
            if elem not in model:
                self.add_error('File "%s", Element "%s" is missing a '
                               'required attribute "%s"' % (file_name,
                                                            cur_elem, elem))
                return_value = False

        for attr in model.keys():
            if (attr not in req_elems and
                attr not in opt_elems and
                    attr not in self._is_valid_anywhere):
                self.add_error('File "%s", Element "%s" has an unknown '
                               'attribute "%s"' % (file_name, cur_elem, attr))

        LOG.debug('%s() - %s' % (KenLog.fcn(), return_value))
        return return_value

    def _validate_array(self, model, req_elems, opt_elems, file_name,
                        cur_elem, return_value):
        LOG.info('%s(): file_name="%s", cur_elem="%s"' % (
            KenLog.fcn(), file_name, cur_elem))

        for idx in range(len(model)):
            obj = model[idx]
            for elem in req_elems:
                if elem not in obj:
                    self.add_error('File "%s", Element "%s[%d]" is missing a '
                                   'required attribute "%s"' % (file_name,
                                                                cur_elem,
                                                                idx,
                                                                elem))
                    return_value = False

            for attr in obj.keys():
                if (attr not in req_elems and
                    attr not in opt_elems and
                        attr not in self._is_valid_anywhere):
                    self.add_error('File "%s", Element "%s[%d]" has an '
                                   'unknown attribute "%s"' % (file_name,
                                                               cur_elem,
                                                               idx,
                                                               attr))

        LOG.debug('%s() - %s' % (KenLog.fcn(), return_value))
        return return_value

    def _create_content(self, version, config_key):
        LOG.info('%s()' % KenLog.fcn())
        content = dict()
        content['product'] = dict()
        content['product']['version'] = int(version)
        config_value = self._get_config_value(version, config_key)
        if config_value:
            content[config_key] = config_value
            return content

        return None

    def _get_config_value(self, version, config_key):
        this_version = 0.0
        for version_dict in self._config_files:
            for key, value in six.iteritems(version_dict):
                if key.lower() == 'version':
                    this_version = value
            if float(this_version) == float(version):
                for key, value in six.iteritems(version_dict):
                    if key.lower() == config_key.lower():
                        return value
        return None

    def _get_dict_from_config_value(self, version, config_key):
        return_value = dict()
        config_value = self._get_config_value(version, config_key)
        if config_value:
            for value in config_value:
                return_value[value['name']] = value
        return return_value
