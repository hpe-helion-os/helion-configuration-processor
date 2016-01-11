#!/bin/bash
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
set -eux

sudo -E python ../Scripts/clean.py
sudo -E python ../Scripts/build.py

# cloudConfig.yml location - each cloud has one
# This is where the topology inputs are located
DEFINITION=<path-to-helion-input-model>/2.0/examples/entry-scale-kvm-vsa/cloudConfig.yml


# This is where the service inputs are located
SERVICE_DIR=<path-to-helion-input-model>/2.0/

# JSON Schema directory location
SCHEMA_DIR=../Data/Site

# If set, persistent_state and stage are written to directory from which CP is run
WRITE_LOCAL=
#WRITE_LOCAL="-w"

# Encryption settings
# -e:  encrypt CP Ansible output and private_data.yml
# -k:  change the encryption key used to encrypt output
# blank:  no encryption
#ENCRYPTION=-e
#ENCRYPTION=-k
ENCRYPTION=

# Refresh generated passwords, -p = refresh, blank = don't reset
#REFRESH_PASSWORDS=-p
REFRESH_PASSWORDS=

# Remove deleted servers from persistent state
#REMOVE_DELETED_SERVERS=-d
REMOVE_DELETED_SERVERS=

# Free unused ip addresses from persistent state
#FREE_UNUSED_ADDRESSES=-f
FREE_UNUSED_ADDRESSES=

# Quiet mode - i.e. don't prompt for input when encrypting.
#QUIET=
QUIET=-q

# Use example encryption keys
if [[ ${QUIET} && ${ENCRYPTION} == "-e" ]]; then
   ENCRYPTION_KEY="-x ConfigProcessor1"
   REKEY=
elif [[ ${QUIET} && ${ENCRYPTION} == "-k" ]]; then
   REKEY="-y ConfigProcessor1"
   ENCRYPTION_KEY="-x ConfigProcessor2"
else
   REKEY=
   ENCRYPTION_KEY=
fi

python ./hlm-cp -s ${SERVICE_DIR} -r ${SCHEMA_DIR} -c ${DEFINITION} ${ENCRYPTION} ${REFRESH_PASSWORDS} ${WRITE_LOCAL} ${QUIET} ${ENCRYPTION_KEY} ${REKEY} ${REMOVE_DELETED_SERVERS} ${FREE_UNUSED_ADDRESSES}
