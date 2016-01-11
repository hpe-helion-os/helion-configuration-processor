#!/usr/bin/python
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
import sys
import os
import string
import subprocess
from subprocess import CalledProcessError

supported_versions = ['1', '1.1', '2']
default_version = 1


def type_to_name(plugin_type):
    if plugin_type == '1':
        return 'Generator'

    if plugin_type == '2':
        return 'Builder'

    if plugin_type == '3':
        return 'Checkpointer'

    if plugin_type == '4':
        return 'Validator'

    if plugin_type == '5':
        return 'Variable'

    if plugin_type == '6':
        return 'Explainer'

    if plugin_type == '7':
        return 'Migrator'

    if plugin_type == '8':
        return 'Finalizer'

    if plugin_type == '9':
        return 'Relationship'

    return plugin_type


def type_to_dir(plugin_type):
    dir = type_to_name(plugin_type).lower() + 's'
    return dir


def get_repo_name():
    try:
        repo_name = subprocess.check_output("git config --file=../.gitreview --get gerrit.project",
                                            shell=True)
    except CalledProcessError as e:
        print 'ERROR: cannot get repo_name %s' % str(e)
        sys.exit(-1)
    repo_name = repo_name.split('/')[-1].split('.')[0]
    return repo_name


def get_input():
    plugin_type = ''
    plugin_name = ''
    plugin_version = ''

    while len(plugin_type) == 0:
        print("Enter a Plugin Type")
        print(" 1 -> generator")
        print(" 2 -> builder")
        print(" 3 -> checkpointer")
        print(" 4 -> validator")
        print(" 5 -> variable")
        print(" 6 -> explainer")
        print(" 7 -> migrator")
        print(" 8 -> finalizer")
        print(" 9 -> relationship")
        print(" q -> quit")
        print("")
        print("Choice: "),

        plugin_type = raw_input()

        try:
            if int(plugin_type) < 1 or int(plugin_type) > 9:
                print('ERROR: Invalid plugin type: %s' % plugin_type)
                plugin_type = ''
        except:
            if plugin_type == 'q':
                sys.exit(0)

            print('ERROR: Invalid plugin type: %s' % plugin_type)
            plugin_type = ''

    plugin_type_name = type_to_name(plugin_type)

    while len(str(plugin_version)) == 0:
        print('Enter the %s Version Number %s [%s] > ' % (
            plugin_type_name, ', '.join(supported_versions), default_version)),
        plugin_version = raw_input()

        if len(str(plugin_version)) == 0:
            plugin_version = default_version

        elif plugin_version not in supported_versions:
            print('ERROR: Invalid Plugin Version: %s' % plugin_version)
            plugin_version = ''

    plugin_version = float(plugin_version)

    while len(plugin_name) == 0:
        print("Enter a %s Name (e.g., HostsFile, Interfaces): > " %
              plugin_type_name),
        plugin_name = raw_input()

    plugin_name = plugin_name
    print('--> Class will be: %s%s' % (plugin_name, plugin_type_name))
    print('\n')

    mnemonic = get_mnemonic_from_name(plugin_name)

    print(
        "Enter a %s Mnemonic (e.g., hosts-file, interfaces): [%s-%s] > " %
        (plugin_type_name, mnemonic, plugin_version)),
    plugin_mnemonic = raw_input()

    if len(plugin_mnemonic) == 0:
        plugin_mnemonic = mnemonic

    if not plugin_mnemonic.endswith(str(plugin_version)):
        plugin_mnemonic += '-%s' % plugin_version

    print('--> Plugin mnemonic will be: %s' % plugin_mnemonic.lower())
    print('\n')

    return plugin_type, plugin_name, plugin_mnemonic, plugin_version


def get_mnemonic_from_name(name):
    mnemonic = []

    for c in name:
        lc = str(c)
        if c in string.uppercase:
            if len(mnemonic) > 0:
                mnemonic.append('-')

        mnemonic.append(lc.lower())

    return ''.join(mnemonic)


def get_cp_path():
    curdir = os.getcwd()

    reponame = get_repo_name()
    pos = curdir.find(reponame)
    if pos == -1:
        print('ERROR: Cannot figure out where I\'m at in the filesystem!')
        sys.exit(-1)

    pos += len(reponame)
    value = curdir[:pos]

    value = os.path.join(value, 'ConfigurationProcessor')
    return value


def get_driver_path():
    curdir = os.getcwd()

    reponame = get_repo_name()
    pos = curdir.find(reponame)
    if pos == -1:
        print('ERROR: Cannot figure out where I\'m at in the filesystem!')
        sys.exit(-1)

    pos += len(reponame)
    value = curdir[:pos]

    value = os.path.join(value, 'Driver')
    return value


def get_plugin_path(plugin_type, plugin_version):
    value = get_cp_path()
    value = os.path.join(value, 'helion_configurationprocessor')
    value = os.path.join(value, 'plugins')
    value = os.path.join(value, type_to_dir(plugin_type))

    if plugin_version > 1:
        version = str(plugin_version).replace('.', '_')
        value = os.path.join(value, version)

    return value


def create_generator(plugin_path, plugin_name, plugin_mnemonic,
                     plugin_version):
    print('==> Creating Generator...'),

    class_file = '%s/%sGenerator.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.GeneratorPlugin \\\n'
             '    import GeneratorPlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sGenerator(GeneratorPlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, models, controllers):\n')
    fp.write('        super(%sGenerator, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, models, '
             'controllers,\n' % plugin_version)
    fp.write('            \'%s\')' % plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def generate(self):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        # TODO - Add Generation Instructions\n')
    fp.write(
        '        LOG.info("Hello from the %sGenerator Plugin")\n' %
        plugin_name)
    fp.write(
        '        print("Hello from the %sGenerator Plugin")\n' % plugin_name)
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def create_builder(plugin_path, plugin_name, plugin_mnemonic, plugin_version):
    print('==> Creating Builder...'),

    class_file = '%s/%sBuilder.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.BuilderPlugin \\\n'
             '    import BuilderPlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sBuilder(BuilderPlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, models, controllers):\n')
    fp.write('        super(%sBuilder, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, models, '
             'controllers,\n' % plugin_version)
    fp.write('            \'%s\')' % plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def build(self):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        # TODO - Add Build Instructions\n')
    fp.write(
        '        LOG.info("Hello from the %sBuilder Plugin")\n' % plugin_name)
    fp.write(
        '        print("Hello from the %sBuilder Plugin")\n' % plugin_name)
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def create_checkpointer(plugin_path, plugin_name, plugin_mnemonic,
                        plugin_version):
    print('==> Creating Checkpointer...'),

    class_file = '%s/%sCheckpointer.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.controller'
             '.CloudNameController '
             '\\\n'
             '    import CloudNameController\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.CheckpointerPlugin '
             '\\\n'
             '    import CheckpointerPlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sCheckpointer(CheckpointerPlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, models, controllers):\n')
    fp.write('        super(%sCheckpointer, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, models, '
             'controllers,\n' % plugin_version)
    fp.write('            \'%s\')' % plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def checkpoint(self):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        path = self._instructions[\'cloud_input_path\']\n')
    fp.write('        cloud_name, nickname = '
             'CloudNameController.get_cloud_names(path)\n')
    fp.write('        self.prepare_filesystem(cloud_name, \'%s\')\n' %
             plugin_name)
    fp.write('\n')
    fp.write('        # TODO - Add Checkpoint Instructions\n')
    fp.write(
        '        LOG.info("Hello from the %sCheckpointer Plugin")\n' %
        plugin_name)
    fp.write(
        '        print("Hello from the %sCheckpointer Plugin")\n' %
        plugin_name)
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def create_validator(plugin_path, plugin_name, plugin_mnemonic,
                     plugin_version):
    print('==> Creating Validator...'),

    class_file = '%s/%sValidator.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.ValidatorPlugin \\\n'
             '    import ValidatorPlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sValidator(ValidatorPlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, config_files):\n')
    fp.write('        super(%sValidator, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, config_files,\n' % plugin_version)
    fp.write('            \'%s\')' % plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def validate(self):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        # TODO - Add Validation Instructions\n')
    fp.write(
        '        LOG.info("Hello from the %sValidator Plugin")\n' %
        plugin_name)
    fp.write(
        '        print("Hello from the %sValidator Plugin")\n' % plugin_name)
    fp.write('\n')
    fp.write('    @property\n')
    fp.write('    def instructions(self):\n')
    fp.write('        return self._instructions\n')
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def create_variable(plugin_path, plugin_name, plugin_mnemonic, plugin_version):
    print('==> Creating Variable...'),

    class_file = '%s/%sVariable.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.VariablePlugin \\\n'
             '    import VariablePlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sVariable(VariablePlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, models, controllers):\n')
    fp.write('        super(%sVariable, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, models, '''
             'controllers,\n' % plugin_version)
    fp.write('            \'%s\')' % plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def calculate(self):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        # TODO - Add Variable Calculation Instructions\n')
    fp.write(
        '        LOG.info("Hello from the %sVariable Plugin")\n' % plugin_name)
    fp.write(
        '        print("Hello from the %sVariable Plugin")\n' % plugin_name)
    fp.write('\n')
    fp.write('        return None\n')
    fp.write('\n')
    fp.write('    @property\n')
    fp.write('    def instructions(self):\n')
    fp.write('        return self._instructions\n')
    fp.write('\n')
    fp.write('    @property\n')
    fp.write('    def models(self):\n')
    fp.write('        return self._models\n')
    fp.write('\n')
    fp.write('    @property\n')
    fp.write('    def controllers(self):\n')
    fp.write('        return self._controllers\n')
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def create_explainer(plugin_path, plugin_name, plugin_mnemonic,
                     plugin_version):
    print('==> Creating Explainer...'),

    class_file = '%s/%sExplainer.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.ExplainerPlugin \\\n'
             '    import ExplainerPlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sExplainer(ExplainerPlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, models, controllers):\n')
    fp.write('        super(%sExplainer, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, models, '
             'controllers,\n' % plugin_version)
    fp.write('            \'%s\')' % plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def explain(self):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        # TODO - Add Explanation\n')
    fp.write(
        '        LOG.info("Hello from the %sExplainer Plugin")\n' %
        plugin_name)
    fp.write(
        '        print("Hello from the %sExplainer Plugin")\n' % plugin_name)
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def create_migrator(plugin_path, plugin_name, plugin_mnemonic, plugin_version):
    print('==> Creating Migrator...'),

    class_file = '%s/%sMigrator.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.MigratorPlugin \\\n'
             '    import MigratorPlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sMigrator(MigratorPlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, models, controllers):\n')
    fp.write('        super(%sMigrator, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, models, '
             'controllers,\n' % plugin_version)
    fp.write('            \'%s\')' % plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def migrate(self, model_name, model):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        # TODO - Add Migration\n')
    fp.write(
        '        LOG.info("Hello from the %sMigrator Plugin")\n' %
        plugin_name)
    fp.write(
        '        print("Hello from the %sMigrator Plugin")\n' % plugin_name)
    fp.write('        return model\n')
    fp.write('\n')
    fp.write('    def applies_to(self):\n')
    fp.write('        return []\n')
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def create_finalizer(plugin_path, plugin_name, plugin_mnemonic,
                     plugin_version):
    print('==> Creating Finalizer...'),

    class_file = '%s/%sFinalizer.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.FinalizerPlugin \\\n'
             '    import FinalizerPlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sFinalizer(FinalizerPlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, models, controllers, config_files):\n')
    fp.write('        super(%sFinalizer, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, models, '
             'controllers,\n' % plugin_version)
    fp.write('            \'%s\')' % plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def finalize(self):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        # TODO - Add Finalize Instructions\n')
    fp.write(
        '        LOG.info("Hello from the %sFinalizer Plugin")\n' %
        plugin_name)
    fp.write(
        '        print("Hello from the %sFinalizer Plugin")\n' % plugin_name)
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def create_relationship(plugin_path, plugin_name, plugin_mnemonic,
                        plugin_version):
    print('==> Creating Relationship...'),

    class_file = '%s/%sRelationship.py' % (plugin_path, plugin_name)
    fp = open(class_file, 'w')
    fp.write('import logging\n')
    fp.write('import logging.config\n')
    fp.write('\n')
    fp.write('from helion_configurationprocessor.cp.model.RelationshipPlugin '
             '\\\n'
             '    import RelationshipPlugin\n')
    fp.write('from helion_configurationprocessor.cp.model.CPLogging \\\n'
             '    import CPLogging as KenLog\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('LOG = logging.getLogger(__name__)\n')
    fp.write('\n')
    fp.write('\n')
    fp.write('class %sRelationship(RelationshipPlugin):\n' % plugin_name)
    fp.write('    def __init__(self, instructions, models, controllers, '
             'model, group,\n')
    fp.write('                 elem_cp, elem_t, additional_services):\n')
    fp.write('        super(%sRelationship, self).__init__(\n' % plugin_name)
    fp.write('            %s, instructions, models, '
             'controllers, model, group, elem_cp,\n' % plugin_version)
    fp.write('            elem_t, additional_services, \'%s\')' %
             plugin_mnemonic)
    fp.write('\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('    def process(self):\n')
    fp.write('        LOG.info(\'%s()\' % KenLog.fcn())\n')
    fp.write('\n')
    fp.write('        # TODO - Add Instructions\n')
    fp.write(
        '        LOG.info("Hello from the %sRelationship Plugin")\n' %
        plugin_name)
    fp.write(
        '        print("Hello from the %sRelationship Plugin")\n' %
        plugin_name)
    fp.write('\n')
    fp.write('    def get_dependencies(self):\n')
    fp.write('        return []\n')
    fp.close()
    print('done.')


def update_setup_py(plugin_type, plugin_name, plugin_mnemonic, plugin_version):
    path = get_cp_path()
    file_name = os.path.join(path, 'setup.py')

    plugin_type_name = type_to_name(plugin_type)

    section = 'helion.configurationprocessor.%s' % plugin_type_name.lower()

    fp_in = open(file_name, 'r')
    lines_in = fp_in.readlines()
    fp_in.close()

    lines_out = []

    i = 0
    while i < len(lines_in):
        line = lines_in[i]
        if section not in line:
            lines_out.append(line)
            i += 1
            continue
        break

    while i < len(lines_in):
        line = lines_in[i]

        if ']' not in line:
            lines_out.append(line)
            i += 1
            continue
        break

    prev_line = lines_out[-1]
    if prev_line.find(',') == -1:
        prev_line = prev_line.replace('\n', ',\n')
    lines_out[-1] = prev_line

    spaces = ' '*12

    lines_out.append('\n')
    lines_out.append('%s\'%s = \'\n' % (spaces, plugin_mnemonic))

    if plugin_version == 1:
        line = '%s\'helion_configurationprocessor.plugins.%ss.\'\n' % \
            (spaces, plugin_type_name.lower())
    else:
        version = str(plugin_version).replace('.', '_')

        line = '%s\'helion_configurationprocessor.plugins.%ss.%s.\'\n' % \
            (spaces, plugin_type_name.lower(), version)

    lines_out.append(line)

    lines_out.append('%s\'%s%s:%s%s\'\n' % (
        spaces, plugin_name, plugin_type_name, plugin_name, plugin_type_name))

    while i < len(lines_in):
        line = lines_in[i]
        lines_out.append(line)
        i += 1

    fp_out = open(file_name, 'w')
    fp_out.write(''.join(lines_out))
    fp_out.close()


def update_hlm_cp(plugin_type, plugin_name, plugin_mnemonic):
    path = get_driver_path()
    file_name = os.path.join(path, 'hlm-cp')

    plugin_type_name = type_to_name(plugin_type)

    section = 'all_%ss' % plugin_type_name.lower()

    fp_in = open(file_name, 'r')
    lines_in = fp_in.readlines()
    fp_in.close()

    lines_out = []

    i = 0
    while i < len(lines_in):
        line = lines_in[i]
        if section not in line:
            lines_out.append(line)
            i += 1
            continue
        break

    while i < len(lines_in):
        line = lines_in[i]

        if ']' not in line:
            lines_out.append(line)
            i += 1
            continue
        break

    prev_line = lines_out[-1]
    if prev_line.find(',') == -1:
        prev_line = prev_line.replace('\n', ',\n')
    lines_out[-1] = prev_line

    num_spaces = prev_line.find('\'')
    spaces = ' '*num_spaces

    lines_out.append('%s\'%s\'\n' % (spaces, plugin_mnemonic))

    while i < len(lines_in):
        line = lines_in[i]
        lines_out.append(line)
        i += 1

    fp_out = open(file_name, 'w')
    fp_out.write(''.join(lines_out))
    fp_out.close()


# MAIN PROCESSING #
def main():
    (plugin_type, plugin_name, plugin_mnemonic, plugin_version) = get_input()

    plugin_path = get_plugin_path(plugin_type, plugin_version)
    if not os.path.exists(plugin_path):
        os.makedirs(plugin_path)

    if plugin_type == '1':
        create_generator(plugin_path, plugin_name, plugin_mnemonic,
                         plugin_version)
    elif plugin_type == '2':
        create_builder(plugin_path, plugin_name, plugin_mnemonic,
                       plugin_version)
    elif plugin_type == '3':
        create_checkpointer(plugin_path, plugin_name, plugin_mnemonic,
                            plugin_version)
    elif plugin_type == '4':
        create_validator(plugin_path, plugin_name, plugin_mnemonic,
                         plugin_version)
    elif plugin_type == '5':
        create_variable(plugin_path, plugin_name, plugin_mnemonic,
                        plugin_version)
    elif plugin_type == '6':
        create_explainer(plugin_path, plugin_name, plugin_mnemonic,
                         plugin_version)
    elif plugin_type == '7':
        create_migrator(plugin_path, plugin_name, plugin_mnemonic,
                        plugin_version)
    elif plugin_type == '8':
        create_finalizer(plugin_path, plugin_name, plugin_mnemonic,
                         plugin_version)
    elif plugin_type == '9':
        create_relationship(plugin_path, plugin_name, plugin_mnemonic,
                            plugin_version)

    update_setup_py(plugin_type, plugin_name, plugin_mnemonic, plugin_version)
    update_hlm_cp(plugin_type, plugin_name, plugin_mnemonic)

if __name__ == '__main__':
    main()
    sys.exit(0)
