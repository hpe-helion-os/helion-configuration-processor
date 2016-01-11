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
# Possible states for a server.  These are used in both the persisted
# state associated with a server ID and for servers currently in the
# model

ALLOCATED = 'allocated'
# Server is in use

AVAILABLE = 'available'
# Server is not currently used and is available for allocation

DELETED = 'deleted'
# A Server with this ID has been previously allocated
# in the cloud but is no longer present in the
# input model


# Behaviour on loading servers in input model
#
# Persisted State      Initial State
# --------------       -------------
# None                 AVAILABLE
# ALLOCATED            ALLOCATED
# DELETED (server)     DELETED
# Any (no server)      None (persisted state updated to mark server as deleted)


# Behaviour during Allocation
#
# Initial State     Cluster Size     Final State
# -------------     ------------     -----------
# ALLOCATED         <= max_size      ALLOCATED
# ALLOCATED         > max_size       ALLOCATED (with warning)
#
# DELETED           < max size       ALLOCATED
# DELETED           >=  max_size     DELETED (with warning)
#
# AVAILABLE         < max_size       ALLOCATED
# AVAILABLE         >= max_size      AVAILABLE
