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
import sh
import six
import sys
import tempfile
import yaml


def get_contents(file_name):
    print('Loading %s' % file_name)

    try:
        fp = open(file_name, 'r')
        lines = fp.readlines()
        fp.close()
    except:
        return None

    fixed_lines = []
    for line in lines:
        if line.find('#') != -1:
            line = line[:line.find('#')]

        fixed_lines.append(line)

    try:
        if file_name.endswith('.json'):
            contents = json.loads(''.join(fixed_lines))
        elif file_name.endswith('.yml') or file_name.endswith('.yaml'):
            contents = yaml.load(''.join(fixed_lines))
        else:
            print('Cannot load file %s' % file_name)
            return None
    except:
        print('Syntax errors detected in file %s' % file_name)
        return None

    return contents


def process_services(service_map, contents):
    for elem_sc in contents['service-components']:
        if 'has-container' in elem_sc:
            for elem_hc in elem_sc['has-container']:
                sn = elem_hc['service-name']
                if is_mnemonic(service_map, sn):
                    elem_hc['service-name'] = mnemonic_to_name(service_map, sn)

        if 'has-proxy' in elem_sc:
            for elem_hp in elem_sc['has-proxy']:
                sn = elem_hp['service-name']
                if is_mnemonic(service_map, sn):
                    elem_hp['service-name'] = mnemonic_to_name(service_map, sn)

        if 'consumes-services' in elem_sc:
            for elem_cs in elem_sc['consumes-services']:
                sn = elem_cs['service-name']
                if is_mnemonic(service_map, sn):
                    elem_cs['service-name'] = mnemonic_to_name(service_map, sn)

        if 'advertises-to-services' in elem_sc:
            for elem_ats in elem_sc['advertises-to-services']:
                sn = elem_ats['service-name']
                if is_mnemonic(service_map, sn):
                    elem_ats['service-name'] = mnemonic_to_name(service_map, sn)

        return contents


def process_control_plane(service_map, contents):
    for elem_t in contents['tiers']:
        for elem_s in elem_t['services']:
            sn = elem_s['name']
            if is_mnemonic(service_map, sn):
                elem_s['name'] = mnemonic_to_name(service_map, sn)

    return contents


def process_cloud_config(service_map, contents):
    if 'control-planes' not in contents:
        return None

    for elem_cp in contents['control-planes']:
        if 'resource-nodes' in elem_cp:
            for elem_rn in elem_cp['resource-nodes']:

                services = []
                for elem_s in elem_rn['services']:
                    if is_mnemonic(service_map, elem_s):
                        services.append(mnemonic_to_name(service_map, elem_s))
                    else:
                        services.append(elem_s)

                elem_rn['services'] = services

    return contents


def process_network_config(service_map, contents):
    if 'logical-interfaces' not in contents:
        return None

    for elem_li in contents['logical-interfaces']:
        if 'logical-networks' not in elem_li:
            return None

        for elem_ln in elem_li['logical-networks']:
            if 'network-traffic' not in elem_ln:
                return None

    return contents


def process_environment_config(service_map, contents):
    if 'node-type' not in contents:
        return None

    for elem_nt in contents['node-type']:
        if 'interface-map' not in elem_nt:
            return None

        for elem_im in elem_nt['interface-map']:
            if 'logical-network-map' not in elem_im:
                return None

            for elem_lnm in elem_im['logical-network-map']:
                if 'ref' in elem_lnm:
                    pass

    return contents


def process_server_config(service_map, contents):
    if 'servers' not in contents:
        return None

    for elem_s in contents['servers']:
        pass

    return contents


def process_network_traffic(service_map, contents):
    for elem_nt in contents['network-traffic']:
        pass

    return contents


def store_contents(file_name, contents):
    print('Storing %s' % file_name)

    fp = open(file_name, 'w')
    if file_name.endswith('.json'):
        json.dump(contents, fp, indent=4)
    elif file_name.endswith('.yml') or file_name.endswith('.yaml'):
        yaml.safe_dump(contents, fp, allow_unicode=False, default_flow_style=False)
    fp.close()


def get_service_map(tmpfile):
    service_map = dict()

    fp = open(tmpfile, 'r')
    lines = fp.readlines()
    fp.close()

    for line in lines:
        tokens = line.split('::')
        name = tokens[0]
        mnemonic = tokens[1].replace('\n', '')

        service_map[name] = mnemonic

    return service_map


def is_name(service_map, service_name):
    for name, mnemonic in six.iteritems(service_map):
        if name == service_name:
            return True

    return False


def is_mnemonic(service_map, service_name):
    for name, mnemonic in six.iteritems(service_map):
        if mnemonic == service_name:
            return True

    return False


def name_to_mnemonic(service_map, service_name):
    for name, mnemonic in six.iteritems(service_map):
        if name == service_name:
            return mnemonic

    return None


def mnemonic_to_name(service_map, service_mnemonic):
    for name, mnemonic in six.iteritems(service_map):
        if mnemonic == service_mnemonic:
            return name

    return None


def main(args):

    if not os.path.exists('services.json'):
        print('Must run this script from Data/Site')
        return -1

    tmpfile = tempfile.mktemp(suffix='.txt')
    print(tmpfile)
    sh.python('../../Scripts/serviceMap.py', '-s', tmpfile)

    service_map = get_service_map(tmpfile)

    exts = ['json', 'yml', 'yaml']
    for ext in exts:
        contents = get_contents('services.%s' % ext)
        if contents:
            contents = process_services(service_map, contents)
            if contents:
                store_contents('services.%s' % ext, contents)

    if os.path.exists('services') and os.path.isdir('services'):
        for root, dirs, files in os.walk('services'):
            for f in files:
                file_name = os.path.join(root, f)
                contents = get_contents(file_name)
                if contents:
                    contents = process_services(service_map, contents)
                    if contents:
                        store_contents(file_name, contents)

    if os.path.exists('../Cloud') and os.path.isdir('../Cloud'):
        file_types = ['ccp', 'rcp', 'scp']
        for root, dirs, files in os.walk('../Cloud'):
            for f in files:
                for ft in file_types:
                    if f.startswith(ft):
                        file_name = os.path.join(root, f)
                        contents = get_contents(file_name)
                        if contents:
                            contents = process_control_plane(
                                service_map, contents)
                            if contents:
                                store_contents(file_name, contents)

    if os.path.exists('../Cloud') and os.path.isdir('../Cloud'):
        for root, dirs, files in os.walk('../Cloud'):
            for f in files:
                if f.find('cloudConfig') != -1 or f.find('CloudConfig') != -1:
                    file_name = os.path.join(root, f)
                    contents = get_contents(file_name)
                    if contents:
                        contents = process_cloud_config(
                            service_map, contents)
                        if contents:
                            store_contents(file_name, contents)

#    if os.path.exists('../Cloud') and os.path.isdir('../Cloud'):
#        for root, dirs, files in os.walk('../Cloud'):
#            for f in files:
#                if (f.find('networkConfig') != -1 or
#                        f.find('NetworkConfig') != -1):
#                    file_name = os.path.join(root, f)
#                    contents = get_contents(file_name)
#                    if contents:
#                        contents = process_network_config(
#                            service_map, contents)
#                        if contents:
#                            store_contents(file_name, contents)

#    if os.path.exists('../Cloud') and os.path.isdir('../Cloud'):
#        for root, dirs, files in os.walk('../Cloud'):
#            for f in files:
#                if (f.find('environmentConfig') != -1 or
#                        f.find('EnvironmentConfig') != -1):
#                    file_name = os.path.join(root, f)
#                    contents = get_contents(file_name)
#                    if contents:
#                        contents = process_environment_config(
#                            service_map, contents)
#                        if contents:
#                            store_contents(file_name, contents)

#    if os.path.exists('../Cloud') and os.path.isdir('../Cloud'):
#        for root, dirs, files in os.walk('../Cloud'):
#            for f in files:
#                if (f.find('serverConfig') != -1 or
#                        f.find('ServerConfig') != -1):
#                    file_name = os.path.join(root, f)
#                    contents = get_contents(file_name)
#                    if contents:
#                        contents = process_server_config(
#                            service_map, contents)
#                        if contents:
#                            store_contents(file_name, contents)

#    exts = ['json', 'yml', 'yaml']
#    for ext in exts:
#        contents = get_contents('network_traffic.%s' % ext)
#        if contents:
#            contents = process_network_traffic(
#                service_map, contents)
#            if contents:
#                store_contents('network_traffic.%s' % ext, contents)
#
#    if os.path.exists('network_traffic') and os.path.isdir('network_traffic'):
#        for root, dirs, files in os.walk('network_traffic'):
#            for f in files:
#                file_name = os.path.join(root, f)
#                contents = get_contents(file_name)
#                if contents:
#                    contents = process_network_traffic(
#                        service_map, contents)
#                    if contents:
#                        store_contents(file_name, contents)

    os.remove(tmpfile)

if __name__ == "__main__":
    main(sys.argv[1:])
