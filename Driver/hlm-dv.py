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
import sys
import getpass

from helion_configurationprocessor.cp.model.CPSecurity \
    import CPSecurity


def _get_options():
    user_instructions = dict()

    user_instructions['encryption_key'] = \
        user_instructions['encryption_key'] = \
        CPSecurity.make_key(
            getpass.getpass(
                'Enter the current key to be used for decryption: '))

    return user_instructions


def _decrypt_file(instructions, file_name):
    fp = open(file_name, 'r')
    lines = fp.readlines()
    fp.close()

    need_to_write = False
    for i in range(len(lines)):
        line = lines[i]
        if line.find('='):
            need_to_write = True

            tokens = line.split()
            for t in tokens:
                if t.endswith('='):
                    plaintext = CPSecurity.decrypt(
                        instructions['encryption_key'], t)
                    if plaintext is None:
                        print('error: Incorrect Decryption Key')
                        sys.exit(-1)

                    lines[i] = line.replace(t, plaintext)

    if need_to_write:
        print('Updating %s' % file_name)
        fp = open(file_name, 'w')
        for line in lines:
            fp.write(line)
        fp.close()


def _decrypt_directory(instructions, directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            file_name = os.path.join(root, f)
            if os.path.isfile(file_name):
                _decrypt_file(instructions, file_name)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: hlm-dv.py <directory>')
        sys.exit(-1)

    instructions = _get_options()

    _decrypt_directory(instructions, sys.argv[1])

    sys.exit(0)
