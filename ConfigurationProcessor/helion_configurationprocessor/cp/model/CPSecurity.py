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
import json
import yaml
import base64
import string

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

from .CPSecurityHelper import CPSecurityHelper


def pad(block_size, s):
    space = block_size - (len(s) % block_size)

    if space < 0:
        return s

    padding = '{'
    data = s + space * padding
    return data


def unpad(s):
    padding = '{'
    data = s.rstrip(padding)
    return data


def ispunct(s):
    return any(c in string.punctuation for c in s)


class CPSecurity(object):

    @classmethod
    def make_key(cls, secret):
        padded_secret = pad(32, secret)
        key = base64.urlsafe_b64encode(padded_secret[:32])
        return key

    @classmethod
    def decode_key(cls, secret):
        dec_secret = unpad(base64.urlsafe_b64decode(secret))
        return dec_secret

    @classmethod
    def encrypt(cls, secret, plaintext):
        f = Fernet(secret)
        return f.encrypt(bytes(plaintext))

    @classmethod
    def decrypt(cls, secret, ciphertext):
        f = Fernet(secret)

        try:
            plaintext = f.decrypt(ciphertext)
            return plaintext
        except InvalidToken:
            return None

    @classmethod
    def validate(cls, cloud_input_path, secret):
        status = True
        messages = []

        min_length = 12
        max_length = 128
        min_categories = 3

        cfg_file = cloud_input_path
        if os.path.exists(cfg_file):
            fp = open(cfg_file, 'r')
            if cfg_file.endswith('.json'):
                contents = json.load(fp)
            elif cfg_file.endswith('.yml') or cfg_file.endswith('.yaml'):
                lines = fp.readlines()
                contents = yaml.load(''.join(lines))
            else:
                status = False
                messages.append('Invalid file format "%s"' % cfg_file)
                fp.close()
                return status, messages

            fp.close()

            key = 'password-validation'
            if key in contents:
                if 'min-length' in contents[key]:
                    min_length = contents[key]['min-length']
                    if min_length < 6:
                        min_length = 6

                if 'max-length' in contents[key]:
                    max_length = contents[key]['max-length']
                    if max_length > 1024:
                        max_length = 1024

                if 'min-categories' in contents[key]:
                    min_categories = contents[key]['min-categories']
                    if min_categories > 4:
                        min_categories = 4

                    if min_categories < 2:
                        min_categories = 2

                if min_length > max_length:
                    status = False
                    messages.append('CONFIGURATION ERROR: Minimum and '
                                    'Maximum password length values are '
                                    'incorrect in %s' % cfg_file)

        dec_secret = unpad(base64.urlsafe_b64decode(secret))

        if len(dec_secret) < min_length:
            status = False
            messages.append('The Encryption Key must be at least %d '
                            'characters' % min_length)

        if len(dec_secret) > max_length:
            status = False
            messages.append('The Encryption Key must be at most %d '
                            'characters' % max_length)

        num_categories = 0
        if any(x.isupper() for x in dec_secret):
            num_categories += 1

        if any(x.islower() for x in dec_secret):
            num_categories += 1

        if any(x.isdigit() for x in dec_secret):
            num_categories += 1

        if ispunct(dec_secret):
            num_categories += 1

        if num_categories < min_categories:
            status = False

            if min_categories < 4:
                messages.append('The Encryption Key must contain at least '
                                '%d of following classes of characters: '
                                'Uppercase Letters, Lowercase Letters, '
                                'Digits, Punctuation' % min_categories)
            else:
                messages.append('The Encryption Key must contain all of '
                                'the following classes of characters: '
                                'Uppercase Letters, Lowercase Letters, '
                                'Digits, Punctuation')

        return status, messages

    @classmethod
    def calculate_complexity(cls, secret):
        ksh = CPSecurityHelper()
        dec_secret = unpad(base64.urlsafe_b64decode(secret))
        return ksh.calculate_complexity(dec_secret)
