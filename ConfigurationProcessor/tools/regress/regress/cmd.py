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
import argparse
import json
import os
import os.path
import sys
import termcolor

from cloud_model import (
    cloudmodel_json,
    group_vars_all,
)

from .comparator import (
    EQUAL,
    WARN,
    ADDITIONAL,
    MISSING,
    DIFFER,

    prefix,
    extension,
    basename,
    directory,

    warn_only,
    null_diff,
    base_diff,
)
from .ansible import ansible_hosts
from .json_diff import (
    json_diff,
    yaml_diff,
)

WARNING = False
ERROR = False


def main():
    parser = argparse.ArgumentParser(
        description='Recursively compare a directory tree')
    parser.add_argument('--quiet', '-q', dest='quiet',
                        action='store_const', const=True,
                        help='suppress OK output')
    parser.add_argument('input', type=str,
                        help='directory to compare against')
    parser.add_argument('compare', type=str,
                        help='directory to compare')

    args = parser.parse_args()
    compare_dir(args.input, args.compare, quiet=args.quiet)
    if WARNING or ERROR:
        return 1
    return 0


def reslice_path(top, prefix, suffix):
    path = os.path.join(prefix, suffix)
    assert path.startswith(top + "/")
    return path[:len(top)], path[len(top) + 1:]


def walk(top_dir):
    result_dirs = []
    result_files = []

    for path, dirs, files in os.walk(top_dir):
        result_dirs += [reslice_path(top_dir, path, d)[1] for d in dirs]
        result_files += [reslice_path(top_dir, path, f)[1] for f in files]

    return result_dirs, result_files


def report(summary, **kwargs):
    print >>sys.stdout, summary, json.dumps(kwargs, indent=2) if kwargs else ""


def warn(summary, **kwargs):
    global WARNING
    report(termcolor.colored(summary, 'yellow'), **kwargs)
    WARNING = True


def error(summary, **kwargs):
    global ERROR
    report(termcolor.colored(summary, 'red'), **kwargs)
    ERROR = True


def compare_dir(in_dir, compare_dir, quiet=False):
    in_dirs, in_files = walk(in_dir)
    comp_dirs, comp_files = walk(compare_dir)

    compare_directory_tree(in_dirs, comp_dirs, quiet=quiet)

    compare_file_tree(in_dir, in_files, compare_dir, comp_files, quiet=quiet)


def compare_directory_tree(in_dirs, comp_dirs, quiet=False):
    s1 = set(in_dirs)
    s2 = set(comp_dirs)

    if s1 == s2:
        return

    if s1 - s2:
        error("Directories missing in the output", missing=sorted(s1 - s2))

    if s2 - s1:
        warn("Directories additionally present", additional=sorted(s2 - s1))


def compare_file_tree(in_dir, in_files, comp_dir, comp_files, quiet=False):
    s1 = set(in_files)
    s2 = set(comp_files)

    LINE = "--------------------------------------------------------"
    for input_file in in_files:
        if input_file not in s2:
            continue

        result, text = compare_file(in_dir, comp_dir, input_file)
        if result == EQUAL:
            if not quiet:
                report(LINE)
                report("OK: " + input_file)
        elif result == ADDITIONAL:
            report(LINE)
            warn("Additional entries: " + input_file)
            report(text)
        elif result == WARN:
            report(LINE)
            warn("WARNING: " + input_file)
            report(text)
        elif result == MISSING:
            report(LINE)
            error("Missing entries: " + input_file)
            report(text)
        elif result == DIFFER:
            report(LINE)
            error("Files differ: " + input_file)
            report(text)

    if s1 - s2:
        report(LINE)
        error("Files missing in output", missing=sorted(s1 - s2))
    if s2 - s1:
        report(LINE)
        warn("Files additionally present", additional=sorted(s2 - s1))


def compare_file(d1, d2, input_file):
    # Locate a comparator.
    return comparator(input_file)(d1, d2, input_file)


def comparator(diff_file):
    for test, comp in COMPARATORS:
        if test(diff_file):
            return comp

    return base_diff


COMPARATORS = [
    (prefix("hlm_logs/"), null_diff),
    (basename("verb_hosts"), ansible_hosts),
    (basename("CloudDiagram.txt"), warn_only(base_diff)),
    (basename("CloudModel.json"), cloudmodel_json),
    (directory("ansible/group_vars") & basename("all"), group_vars_all),
    (directory("ansible/group_vars"), yaml_diff),
    (extension(".json"), json_diff),
    (extension(".yaml"), yaml_diff),
    (extension(".yml"), yaml_diff),
]
