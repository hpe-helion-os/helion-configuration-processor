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
import fnmatch
import os
import sh

from .utils import read_file


EQUAL = 0
ADDITIONAL = 1
WARN = 2
MISSING = 3
DIFFER = 4


class Condition(object):
    def __init__(self, f):
        self.f = f

    def __and__(f1, f2):
        return Condition(lambda fn: f1.f(fn) and f2.f(fn))

    def __or__(f1, f2):
        return Condition(lambda fn: f1.f(fn) or f2.f(fn))

    def __neg__(self):
        return Condition(lambda fn: not self.f(fn))

    def __call__(self, x):
        return self.f(x)


def condition(f):
    def fn(arg):
        return Condition(f(arg))
    return fn


@condition
def prefix(p):
    return lambda(fn): fn.startswith(p)


@condition
def extension(e):
    return lambda(fn): os.path.splitext(fn)[1] == e


@condition
def basename(f):
    return lambda(fn): os.path.basename(fn) == f


@condition
def glob(g):
    return lambda(fn): fnmatch.fnmatch(fn, g)


@condition
def directory(d):
    """Return true if the file lives inside a tree that ends with d"""
    d = "/" + d
    return lambda(fn): ("/" + os.path.split(fn)[0]).endswith(d)


def null_diff(d1, d2, file):
    return EQUAL, None


def base_diff(d1, d2, file):
    c1 = read_file(d1, file)
    c2 = read_file(d2, file)

    if c1 == c2:
        return EQUAL, None

    result = sh.diff("-u", os.path.join(d1, file),
                     os.path.join(d2, file), _ok_code=[0, 1])
    return DIFFER, str(result)


def warn_only(fn=base_diff):
    def diff(d1, d2, file):
        result, text = fn(d1, d2, file)
        if result != EQUAL:
            result = WARN
        return result, text
    return diff
