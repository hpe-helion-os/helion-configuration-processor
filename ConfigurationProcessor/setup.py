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
from setuptools import setup, find_packages

setup(
    name='helion_configurationprocessor',
    version='0.2.0',
    author='HP Helion',
    author_email='hp_helion@hp.com',
    packages=find_packages(),
    include_package_data=True,
    scripts=[],
    url='http://www.hp.com',
    license='LICENSE.txt',
    description='Configuration Processor for HP Helion',
    long_description=open('README.txt').read(),
    install_requires=['six', 'stevedore', 'netaddr', 'pycrypto',
                      'cryptography', 'simplejson', 'jsonschema',
                      'pbs' if os.name == 'nt' else 'sh'],
    zip_safe=False,
    entry_points={
        'helion.configurationprocessor.generator': [
            'cloud-init = '
            'helion_configurationprocessor.plugins.generators.'
            'CloudGenerator:CloudGenerator',

            'machine-init = '
            'helion_configurationprocessor.plugins.generators.'
            'MachineGenerator:MachineGenerator',

            'network-init = '
            'helion_configurationprocessor.plugins.generators.'
            'NetworkGenerator:NetworkGenerator',

            'cfg-vars = '
            'helion_configurationprocessor.plugins.generators.'
            'CfgVarsGenerator:CfgVarsGenerator',

            'control-plane-init = '
            'helion_configurationprocessor.plugins.generators.'
            'ControlPlaneGenerator:ControlPlaneGenerator',

            'member-init = '
            'helion_configurationprocessor.plugins.generators.'
            'MemberGenerator:MemberGenerator',

            'resource-node-init = '
            'helion_configurationprocessor.plugins.generators.'
            'ResourceNodeGenerator:ResourceNodeGenerator',

            'service-init = '
            'helion_configurationprocessor.plugins.generators.'
            'ServiceGenerator:ServiceGenerator',

            'network-ref-init = '
            'helion_configurationprocessor.plugins.generators.'
            'NetworkRefGenerator:NetworkRefGenerator',

            'network-topology-init = '
            'helion_configurationprocessor.plugins.generators.'
            'NetworkTopologyGenerator:NetworkTopologyGenerator',

            'node-init = '
            'helion_configurationprocessor.plugins.generators.'
            'NodeGenerator:NodeGenerator',

            'baremetal-init = '
            'helion_configurationprocessor.plugins.generators.'
            'BaremetalGenerator:BaremetalGenerator',

            'server-init = '
            'helion_configurationprocessor.plugins.generators.'
            'ServerGenerator:ServerGenerator',

            'server-allocation = '
            'helion_configurationprocessor.plugins.generators.'
            'ServerAllocationGenerator:ServerAllocationGenerator',

            'environment-init = '
            'helion_configurationprocessor.plugins.generators.'
            'EnvironmentGenerator:EnvironmentGenerator',

            'external-services = '
            'helion_configurationprocessor.plugins.generators.'
            'ExternalServicesGenerator:ExternalServicesGenerator',

            'encryption-key = '
            'helion_configurationprocessor.plugins.generators.'
            'EncryptionKeyGenerator:EncryptionKeyGenerator',

            'node-type = '
            'helion_configurationprocessor.plugins.generators.'
            'NodeTypeGenerator:NodeTypeGenerator',

            'service-var-overrides = '
            'helion_configurationprocessor.plugins.generators.'
            'ServiceVarOverridesGenerator:ServiceVarOverridesGenerator',

            'network-repo-address = '
            'helion_configurationprocessor.plugins.generators.'
            'NetworkRepoAddressGenerator:NetworkRepoAddressGenerator',

            'failure-zone-1.0 = '
            'helion_configurationprocessor.plugins.generators.'
            'FailureZoneGenerator:FailureZoneGenerator',

            'cloud-cplite-2.0 = '
            'helion_configurationprocessor.plugins.generators.2_0.'
            'CloudCpLiteGenerator:CloudCpLiteGenerator',

            'consumes-generator-2.0 = '
            'helion_configurationprocessor.plugins.generators.2_0.'
            'ConsumesGenerator:ConsumesGenerator',

            'route-generator-2.0 = '
            'helion_configurationprocessor.plugins.generators.2_0.'
            'RouteGenerator:RouteGenerator',

            'ring-specifications-2.0 = '
            'helion_configurationprocessor.plugins.generators.2_0.'
            'RingSpecificationsGenerator:RingSpecificationsGenerator',

            'firewall-generator-2.0 = '
            'helion_configurationprocessor.plugins.generators.2_0.'
            'FirewallGenerator:FirewallGenerator'
        ],

        'helion.configurationprocessor.builder': [
            'ans-all-vars = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.AnsAllVarsBuilder:AnsAllVarsBuilder',

            'ans-group-vars = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.AnsGroupVarsBuilder:AnsGroupVarsBuilder',

            'ans-host-vars = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.AnsHostVarsBuilder:AnsHostVarsBuilder',

            'ans-hosts = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.AnsHostsBuilder:AnsHostsBuilder',

            'ans-config = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.AnsConfigBuilder:AnsConfigBuilder',

            'ans-verb-hosts = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.AnsVerbHostsBuilder:AnsVerbHostsBuilder',

            'ans-encr-artifacts = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.AnsEncryptArtifactsBuilder:AnsEncryptArtifactsBuilder',

            'ans-tlpb-commit = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.TopLevelPlaybooks.'
            'AnsCommitBuilder:AnsCommitBuilder',

            'ans-tlpb-verb = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.TopLevelPlaybooks.'
            'AnsVerbBuilder:AnsVerbBuilder',

            'ans-tlpb-action = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.TopLevelPlaybooks.'
            'AnsActionBuilder:AnsActionBuilder',

            'ans-carrier-grade-verb-1.0 = '
            'helion_configurationprocessor.plugins.builders.'
            'Ansible.TopLevelPlaybooks.'
            'AnsCarrierGradeVerbBuilder:AnsCarrierGradeVerbBuilder',

            'diagram = '
            'helion_configurationprocessor.plugins.builders.'
            'Diagram.DiagramBuilder:DiagramBuilder',

            'hosts-file = '
            'helion_configurationprocessor.plugins.builders.'
            'Network.HostsFileBuilder:HostsFileBuilder',

            'interfaces = '
            'helion_configurationprocessor.plugins.builders.'
            'Network.InterfacesBuilder:InterfacesBuilder',

            'pci-bus-enumeration = '
            'helion_configurationprocessor.plugins.builders.'
            'Network.PciBusEnumerationBuilder:PciBusEnumerationBuilder',

            'ic2-zone-hosts = '
            'helion_configurationprocessor.plugins.builders.'
            'Icinga.Ic2ZoneHostsBuilder:Ic2ZoneHostsBuilder',

            'ic2-zone-services = '
            'helion_configurationprocessor.plugins.builders.'
            'Icinga.Ic2ZoneServicesBuilder:Ic2ZoneServicesBuilder',

            'ic2-zone-templates = '
            'helion_configurationprocessor.plugins.builders.'
            'Icinga.Ic2ZoneTemplatesBuilder:Ic2ZoneTemplatesBuilder',

            'fs-prep = '
            'helion_configurationprocessor.plugins.builders.'
            'Internal.FileSystemPrepBuilder:FileSystemPrepBuilder',

            'server-addresses = '
            'helion_configurationprocessor.plugins.builders.'
            'ServerAddressesBuilder:ServerAddressesBuilder',

            'service-block-overrides = '
            'helion_configurationprocessor.plugins.builders.'
            'ServiceBlockOverridesBuilder:ServiceBlockOverridesBuilder',

            'wr-config-1.0 = '
            'helion_configurationprocessor.plugins.builders.'
            'WindRiver.WRConfigBuilder:WRConfigBuilder',

            'hosts-file-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'HostsFileBuilder:HostsFileBuilder',

            'ansible-hosts-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'AnsibleHostsBuilder:AnsibleHostsBuilder',

            'ansible-all-vars-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'AnsibleAllVarsBuilder:AnsibleAllVarsBuilder',

            'ans-host-vars-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'AnsHostVarsBuilder:AnsHostVarsBuilder',

            'ans-group-vars-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'AnsGroupVarsBuilder:AnsGroupVarsBuilder',

            'net-info-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'NetworkInfoBuilder:NetworkInfoBuilder',

            'route-info-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'RouteInfoBuilder:RouteInfoBuilder',

            'server-info-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'ServerInfoBuilder:ServerInfoBuilder',

            'firewall-info-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'FirewallInfoBuilder:FirewallInfoBuilder',

            'diagram-2.0 = '
            'helion_configurationprocessor.plugins.builders.2_0.'
            'DiagramBuilder:DiagramBuilder'
        ],

        'helion.configurationprocessor.validator': [
            'cloudarch = '
            'helion_configurationprocessor.plugins.validators.'
            'CloudArchitectureValidator:CloudArchitectureValidator',

            'cloudconfig = '
            'helion_configurationprocessor.plugins.validators.'
            'CloudConfigValidator:CloudConfigValidator',

            'controlplane = '
            'helion_configurationprocessor.plugins.validators.'
            'ControlPlaneValidator:ControlPlaneValidator',

            'environmentconfig = '
            'helion_configurationprocessor.plugins.validators.'
            'EnvironmentConfigValidator:EnvironmentConfigValidator',

            'machine-architecture = '
            'helion_configurationprocessor.plugins.validators.'
            'MachineArchitectureValidator:MachineArchitectureValidator',

            'networkconfig = '
            'helion_configurationprocessor.plugins.validators.'
            'NetworkConfigValidator:NetworkConfigValidator',

            'baremetalconfig = '
            'helion_configurationprocessor.plugins.validators.'
            'BaremetalConfigValidator:BaremetalConfigValidator',

            'serverconfig = '
            'helion_configurationprocessor.plugins.validators.'
            'ServerConfigValidator:ServerConfigValidator',

            'icinga = '
            'helion_configurationprocessor.plugins.validators.'
            'IcingaValidator:IcingaValidator',

            'ansible = '
            'helion_configurationprocessor.plugins.validators.'
            'AnsibleValidator:AnsibleValidator',

            'logical-network = '
            'helion_configurationprocessor.plugins.validators.'
            'LogicalNetworkValidator:LogicalNetworkValidator',

            'encryption-key = '
            'helion_configurationprocessor.plugins.validators.'
            'EncryptionKeyValidator:EncryptionKeyValidator',

            'fs-prep = '
            'helion_configurationprocessor.plugins.validators.'
            'FileSystemPrepValidator:FileSystemPrepValidator',

            'node-type = '
            'helion_configurationprocessor.plugins.validators.'
            'NodeTypeValidator:NodeTypeValidator',

            'disk-model-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'DiskModelValidator:DiskModelValidator',

            'cloudconfig-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'CloudConfigValidator:CloudConfigValidator',

            'interface-models-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'InterfaceModelsValidator:InterfaceModelsValidator',

            'network-groups-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'NetworkGroupsValidator:NetworkGroupsValidator',

            'networks-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'NetworksValidator:NetworksValidator',

            'server-roles-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'ServerRolesValidator:ServerRolesValidator',

            'server-groups-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'ServerGroupsValidator:ServerGroupsValidator',

            'servers-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'ServersValidator:ServersValidator',

            'control-planes-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'ControlPlanesValidator:ControlPlanesValidator',

            'nic-mappings-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'NicMappingsValidator:NicMappingsValidator',

            'pass-through-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'PassThroughValidator:PassThroughValidator',

            'ring-specifications-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'RingSpecificationsValidator:RingSpecificationsValidator',

            'firewall-rules-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'FirewallRulesValidator:FirewallRulesValidator',

            'cross-reference-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'CrossReferenceValidator:CrossReferenceValidator',

            'deployer-network-lifecycle-mgr-2.0 = '
            'helion_configurationprocessor.plugins.validators.2_0.'
            'DeployerNetworkLifecycleMgrValidator:DeployerNetworkLifecycleMgrValidator'
        ],

        'helion.configurationprocessor.variable': [
            'control-plane-id = '
            'helion_configurationprocessor.plugins.variables.'
            'ControlPlaneIdVariable:ControlPlaneIdVariable',

            'control-plane-prefix = '
            'helion_configurationprocessor.plugins.variables.'
            'ControlPlanePrefixVariable:ControlPlanePrefixVariable',

            'failure-zone = '
            'helion_configurationprocessor.plugins.variables.'
            'FailureZoneVariable:FailureZoneVariable',

            'host-address = '
            'helion_configurationprocessor.plugins.variables.'
            'HostAddressVariable:HostAddressVariable',

            'host-name = '
            'helion_configurationprocessor.plugins.variables.'
            'HostNameVariable:HostNameVariable',

            'member-id = '
            'helion_configurationprocessor.plugins.variables.'
            'MemberIdVariable:MemberIdVariable',

            'member-in-tier = '
            'helion_configurationprocessor.plugins.variables.'
            'MemberInTierVariable:MemberInTierVariable',

            'random-password = '
            'helion_configurationprocessor.plugins.variables.'
            'RandomPasswordVariable:RandomPasswordVariable',

            'random-string = '
            'helion_configurationprocessor.plugins.variables.'
            'RandomStringVariable:RandomStringVariable',

            'tier-id = '
            'helion_configurationprocessor.plugins.variables.'
            'TierIdVariable:TierIdVariable',

            'tier-prefix = '
            'helion_configurationprocessor.plugins.variables.'
            'TierPrefixVariable:TierPrefixVariable',

            'sequence-number = '
            'helion_configurationprocessor.plugins.variables.'
            'SequenceNumberVariable:SequenceNumberVariable',

            'random-password-2.0 = '
            'helion_configurationprocessor.plugins.variables.2_0.'
            'RandomPasswordVariable:RandomPasswordVariable',

            'random-string-2.0 = '
            'helion_configurationprocessor.plugins.variables.2_0.'
            'RandomStringVariable:RandomStringVariable',

            'sequence-number-2.0 = '
            'helion_configurationprocessor.plugins.variables.2_0.'
            'SequenceNumberVariable:SequenceNumberVariable'
        ],

        'helion.configurationprocessor.checkpointer': [
            'desired-state = '
            'helion_configurationprocessor.plugins.checkpointers.'
            'DesiredStateCheckpointer:DesiredStateCheckpointer',

            'config = '
            'helion_configurationprocessor.plugins.checkpointers.'
            'ConfigCheckpointer:ConfigCheckpointer',

            'persistent-state = '
            'helion_configurationprocessor.plugins.checkpointers.'
            'PersistentStateCheckpointer:PersistentStateCheckpointer'
        ],

        'helion.configurationprocessor.explainer': [
            'cloud-structure = '
            'helion_configurationprocessor.plugins.explainers.'
            'CloudStructureExplainer:CloudStructureExplainer',

            'services = '
            'helion_configurationprocessor.plugins.explainers.'
            'ServicesExplainer:ServicesExplainer',

            'network-traffic-groups = '
            'helion_configurationprocessor.plugins.explainers.'
            'NetworkTrafficGroupsExplainer:NetworkTrafficGroupsExplainer',

            'servers = '
            'helion_configurationprocessor.plugins.explainers.'
            'ServersExplainer:ServersExplainer',

            'override-vars = '
            'helion_configurationprocessor.plugins.explainers.'
            'OverrideVarsExplainer:OverrideVarsExplainer',

            'override-blocks = '
            'helion_configurationprocessor.plugins.explainers.'
            'OverrideBlocksExplainer:OverrideBlocksExplainer',

            'servers-2.0 = '
            'helion_configurationprocessor.plugins.explainers.2_0.'
            'ServersExplainer:ServersExplainer'
        ],

        'helion.configurationprocessor.migrator': [
            'service-name-to-mnemonic = '
            'helion_configurationprocessor.plugins.migrators.'
            'ServiceNameToMnemonicMigrator:ServiceNameToMnemonicMigrator',

            'service-name-to-mnemonic-2.0 = '
            'helion_configurationprocessor.plugins.migrators.2_0.'
            'ServiceNameToMnemonicMigrator:ServiceNameToMnemonicMigrator',

            'resource-nodes-to-resources-2.0 = '
            'helion_configurationprocessor.plugins.migrators.2_0.'
            'ResourceNodesMigrator:ResourceNodesMigrator'
        ],

        'helion.configurationprocessor.finalizer': [
            'cloud-model-1.0 = '
            'helion_configurationprocessor.plugins.finalizers.'
            'CloudModelFinalizer:CloudModelFinalizer',

            'service-map-1.0 = '
            'helion_configurationprocessor.plugins.finalizers.'
            'ServiceMapFinalizer:ServiceMapFinalizer',

            'network-map-1.0 = '
            'helion_configurationprocessor.plugins.finalizers.'
            'NetworkMapFinalizer:NetworkMapFinalizer',

            'node-map-1.0 = '
            'helion_configurationprocessor.plugins.finalizers.'
            'NodeMapFinalizer:NodeMapFinalizer',

            'cloud-model-2.0 = '
            'helion_configurationprocessor.plugins.finalizers.2_0.'
            'CloudModelFinalizer:CloudModelFinalizer',

            'service-view-2.0 = '
            'helion_configurationprocessor.plugins.finalizers.2_0.'
            'ServiceViewFinalizer:ServiceViewFinalizer',

            'address-allocation-2.0 = '
            'helion_configurationprocessor.plugins.finalizers.2_0.'
            'AddressAllocationFinalizer:AddressAllocationFinalizer'
        ],

        'helion.configurationprocessor.relationship': [
            'produces-log-files-1.0 = '
            'helion_configurationprocessor.plugins.relationships.'
            'ProducesLogFilesRelationship:ProducesLogFilesRelationship',

            'consumes-1.0 = '
            'helion_configurationprocessor.plugins.relationships.'
            'ConsumesRelationship:ConsumesRelationship',

            'has-proxy-1.0 = '
            'helion_configurationprocessor.plugins.relationships.'
            'HasProxyRelationship:HasProxyRelationship',

            'advertises-1.0 = '
            'helion_configurationprocessor.plugins.relationships.'
            'AdvertisesRelationship:AdvertisesRelationship',

            'has-container-1.0 = '
            'helion_configurationprocessor.plugins.relationships.'
            'HasContainerRelationship:HasContainerRelationship'
        ]
    }
)
