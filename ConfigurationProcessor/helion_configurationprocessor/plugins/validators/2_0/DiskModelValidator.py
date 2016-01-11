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
import logging.config
import re

from helion_configurationprocessor.cp.model.ValidatorPlugin \
    import ValidatorPlugin
from helion_configurationprocessor.cp.model.CPLogging \
    import CPLogging as KenLog

LOG = logging.getLogger(__name__)


class DiskModelValidator(ValidatorPlugin):
    def __init__(self, instructions, config_files):
        super(DiskModelValidator, self).__init__(
            2.0, instructions, config_files,
            'disk-model-2.0')
        self._valid = False
        LOG.info('%s()' % KenLog.fcn())

    def validate(self):
        LOG.info('%s()' % KenLog.fcn())

        version = float(self.version())

        input = self._create_content(version, "disk-models")
        self._valid = self.validate_schema(input, "disk_model")

        if self._valid:
            disk_models = input['disk-models']
            self._validate_names(disk_models)
            self._prevent_device_duplication(disk_models)
            self._validate_vg_space(disk_models)
            self._validate_mode_bits(disk_models)

        return self._valid

    def _mode_bits_parser(self, mode, error_msg):
        if not re.match(r"(^[ugoa]*[-+=]([rwxXst]*|[ugo])"
                        "(,[ugoa]*[-+=]([rwxXst]*|[ugo]))*$)|"
                        "(^[0-7]{4}$)", str(mode)):
            self.add_error(error_msg)
            self._valid = False

    def _validate_mode_bits(self, disk_models):
        # Check if mode bits are valid if set for lv and pv volumes.
        for model in disk_models:
            for vg in model['volume-groups']:

                for lv in vg['logical-volumes']:
                    if 'mode' in lv:
                        msg = ("Disk model '{dmName}' with volume "
                               "group '{vgName}' has invalid root mode "
                               "bits set '{lvMode}' on disk '{lvName}'"
                               ).format(dmName=model['name'],
                                        vgName=vg['name'],
                                        lvMode=lv['mode'],
                                        lvName=lv['name'])
                        self._mode_bits_parser(lv['mode'], msg)

                for pv in vg['physical-volumes']:
                    if 'mode' in pv:
                        msg = ("Disk model {dmName} has invalid root mode "
                               "bits set '{pvMode}' on device '{pvDevice}'"
                               ).format(dmName=model['name'],
                                        pvMode=pv['mode'],
                                        pvDevice=pv['device'])
                        self._mode_bits_parser(pv['mode'], msg)

    def _validate_vg_space(self, disk_models):
        # Check if 5% of space has been left in the volume group to
        # allow for LVM snapshot.
        for model in disk_models:
            for vg in model['volume-groups']:
                space = 0
                for lv in vg['logical-volumes']:
                    space += int(lv['size'].replace('%', ''))
                    if space > 95:
                        msg = ("Volume group %s in disk model %s "
                               "has less that 5%% unallocated space "
                               "which is the minimum recommended "
                               "to allow snapshots to "
                               "be taken." % (model['name'], vg['name']))
                        self.add_warning(msg)
                        return

    def _validate_names(self, disk_models):

        #
        # Check each model is only defined once
        #
        names = set()
        for model in disk_models:
            if model['name'] in names:
                msg = ("Disk model %s is defined more than once." %
                       (model['name']))
                self.add_error(msg)
                self._valid = False
            else:
                names.add(model['name'])

    def _prevent_device_duplication(self, disk_models):

        #
        # Check that disk device is not in more than one VG or device group.
        #
        for model in disk_models:
            devices = set()
            if 'volume-groups' in model.keys():
                for vg in model['volume-groups']:
                    for pv in vg['physical-volumes']:
                        if pv in devices:
                            self.add_error(("Device %s is defined more "
                                            "than once in %s. This will "
                                            "lead to data corruption."
                                            % (pv, model['name'])))
                            self._valid = False
                            continue
                        else:
                            devices.add(pv)
            if 'device-groups' in model.keys():
                for dg in model['device-groups']:
                    for device in dg['devices']:
                        if device['name'] in devices:
                            self.add_error(("Device %s is defined more "
                                            "than once in %s. This will "
                                            "lead to data corruption."
                                            % (device['name'], model['name'])))
                            self._valid = False
                            continue
                        else:
                            devices.add(device['name'])

    @property
    def instructions(self):
        return self._instructions

    def get_dependencies(self):
        return []
