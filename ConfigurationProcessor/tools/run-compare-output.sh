#!/bin/bash -e
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

USAGE_STRING="
Compares CP output between previous revision and latest

Usage: $(basename $0) [-r <version>] [<configfile>]

    <configfile>                    Alternative cloud config file to pass to
                                    the comparison tests.

    -r, --run-version <version>     Which version of CP to run, can be 1.0 or
                                    2.0. Default is 2.0

    -h, --help                      Displays this help message

"
declare -a VALID_RUN_VERSIONS=("1.0" "2.0")
RUN_VERSION="2.0"
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOPDIR=$(dirname ${SCRIPTDIR})

in_array() {
    local haystack=${1}[@]
    local needle=${2}
    for i in ${!haystack}; do
        if [[ ${i} == ${needle} ]]; then
            return 0
        fi
    done
    return 1
}

#
# Parse arguments
#   Copied and adapted from /usr/share/doc/util-linux/examples/getopt-parse.bash
#
short_opts="r:hc:"
long_opts="run-version:,help,config:"
TEMP=$(getopt -o ${short_opts} --long ${long_opts} -n "${0}" -- "$@")

[[ $? != 0 ]] && { echo "Terminating..." >&2 ; exit 2 ; }

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"

while true ; do
    case "$1" in
        -r|--run-version)
            RUN_VERSION="${2}"
            shift 2
        ;;
        -h|--help)
            echo "${USAGE_STRING}"
            exit 0
        ;;
        -c|--config)
            if [[ -n "${CONFIG_FILE}" ]]
            then
                echo "Can only take one argument for a cloud config file" >&2
                exit 2
            fi
            CONFIG_FILE="${2}"
            shift 2
        ;;
        --)
            shift
            break
        ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 2
        ;;
        *)
            echo "Invalid argument. -$OPTARG not recongised"
            exit 2
        ;;
    esac
done

# check inputs
if [[ -n "${CONFIG_FILE}" ]]
then
    set +e
    REAL_CONFIG_FILE=$(readlink -e ${CONFIG_FILE})
    set -e
    if [[ -z "${REAL_CONFIG_FILE}" ]]
    then
        echo "Specified file '${CONFIG_FILE}' cannot be resolved or does not exist!" >&2
        exit 2
    else
        CONFIG_FILE="${REAL_CONFIG_FILE}"
    fi
fi

if ! in_array VALID_RUN_VERSIONS "${RUN_VERSION}"
then
    echo "Invalid run version provided '${RUN_VERSION}'" >&2
    echo "Must be one of '${VALID_RUN_VERSIONS[@]}'." >&2
    exit 2
fi

# set up options
OPTIONS=""
if [[ -n "${CONFIG_FILE}" ]]
then
    OPTIONS="-- -c ${CONFIG_FILE}"
    case ${RUN_VERSION} in
        "2.0")
            OPTIONS="${OPTIONS} -r ../Data/Site"
            OPTIONS="${OPTIONS} -s .test/hlm-input-model/2.0/"
            ;;
        "1.0")
            OPTIONS="${OPTIONS} -s ../Data/Site"
            ;;
    esac
fi
# switch to the directory above this script so we can run tox directly
cd $(dirname "$(dirname ${0})")

# switch to the directory above this script so we can
# perform actions relative to CP and run tox directly
cd ${TOPDIR}
rm -fr .test
mkdir -p .test
pushd .test

BRANCH=${ZUUL_BRANCH:-hp/master}
PROJECT=${ZUUL_PROJECT:-hp/kenobi-configuration-processor}

if [ -e /usr/zuul-env/bin/zuul-cloner ];
then
    /usr/zuul-env/bin/zuul-cloner \
        -m ../tools/run-compare-clonemap.yaml \
        --cache-dir /opt/git ${GIT_MIRROR:-https://review.hpcloud.net/p} \
        --project-branch hp/hlm-input-model=${BRANCH} \
        hp/hlm-input-model
else
    git clone --depth 1 --single-branch -b ${BRANCH} \
        https://review.hpcloud.net/p/hp/hlm-input-model hlm-input-model
fi
popd

[[ "${PROJECT}" == "hp/hlm-input-model" ]] && PUSHD=${PWD}/hlm-input-model

[[ -n "${PUSHD}" ]] && pushd ${PUSHD}
# try to get a branch name for developers, but fall back to SHA's for CI
GITHEAD=$(git name-rev --no-undefined --name-only HEAD 2>/dev/null || git rev-parse HEAD)
echo "Saving branch to restore '${GITHEAD}'"

# First generate output from HEAD~1
git checkout HEAD~1
[[ -n "${PUSHD}" ]] && popd

tox -e compare-output-old ${OPTIONS}

# Then use that as a reference to compare against HEAD
[[ -n "${PUSHD}" ]] && pushd ${PUSHD}
git checkout ${GITHEAD}
[[ -n "${PUSHD}" ]] && popd

tox -e compare-output-new ${OPTIONS}

# Then use the local regress tool
tox -e regress
