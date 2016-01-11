(c) Copyright 2015 Hewlett Packard Enterprise Development Company LP

Confidential computer software. Valid license from HPE required for
possession, use or copying. Consistent with FAR 12.211 and 12.212,
Commercial Computer Software, Computer Software Documentation, and
Technical Data for Commercial Items are licensed to the U.S.
Government under vendor's standard commercial license.

A smarter diff tool for regression tests.

This basically does a recursive diff over an exemplar and
an output directory tree. It has a small number of plugins
that know how to diff various types of file specifically -
ini-style files, ansible group-style files, and json
and yaml, in particular.

It can be relatively smart about reporting differences:
typically the approach the tool takes is that additions
generate warnings, whereas missing or changed elements
generate errors.

