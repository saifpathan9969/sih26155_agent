"""
GAACA Dataset — Switch Configuration Generators
=================================================
20 vendor generators for enterprise & data-center switch configurations.
Each produces secure, misconfigured, and edge_case variants.
"""

from __future__ import annotations
import json
from generators.base import ConfigGenerator


# =============================================================================
# 1. Cisco IOS Switch (Catalyst)
# =============================================================================
class CiscoIOSSwitchGenerator(ConfigGenerator):
    vendor = "Cisco"
    platform = "IOS-XE"
    model = "9300"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'STP', 'PORT_SECURITY', 'DHCP_SNOOPING']
    product = "Catalyst 9300 / 3850"
    os_name = "Cisco IOS-XE / IOS"
    os_version = "17.x"
    device_type = "switch"
    category = "switch"
    config_format = "cisco_ios_cli"
    vendor_dir_name = "cisco_ios_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""! GAACA Dataset — Cisco Catalyst Switch — SECURE — Sample {index}
version 17.6
service password-encryption
hostname {hn}
!
spanning-tree mode rapid-pvst
spanning-tree portfast default
spanning-tree portfast bpduguard default
spanning-tree extend system-id
!
ip dhcp snooping
ip dhcp snooping vlan {vlan}
no ip dhcp snooping information option
ip arp inspection vlan {vlan}
!
vlan {vlan}
 name Corporate-Data
!
vlan 999
 name Blackhole-Unused
!
interface GigabitEthernet1/0/1
 description Access-Workstation
 switchport mode access
 switchport access vlan {vlan}
 switchport port-security
 switchport port-security maximum 2
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 10.0
 storm-control action shutdown
 spanning-tree bpduguard enable
 no shutdown
!
interface GigabitEthernet1/0/24
 description Core-Trunk-Uplink
 switchport mode trunk
 switchport trunk allowed vlan {vlan},999
 switchport nonegotiate
 ip dhcp snooping trust
 ip arp inspection trust
 no shutdown
!
interface range GigabitEthernet1/0/2 - 23
 switchport mode access
 switchport access vlan 999
 shutdown
!
username secadmin privilege 15 secret {pwd}
ip ssh version 2
no ip http server
ip http secure-server
logging host {syslog}
ntp server {ntp}
!
line vty 0 4
 transport input ssh
 exec-timeout 5 0
!
end
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco Catalyst Switch — MISCONFIGURED — Sample {index}
hostname {hn}
enable password cisco
username admin privilege 15 password admin
!
no spanning-tree portfast bpduguard default
no ip dhcp snooping
!
interface GigabitEthernet1/0/1
 switchport mode dynamic desirable
!
interface range GigabitEthernet1/0/2 - 24
 switchport mode access
 no shutdown
!
ip http server
no ip http secure-server
snmp-server community public rw
!
line vty 0 4
 password cisco
 login
 transport input telnet
!
end
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco Catalyst Switch — EDGE CASE — Sample {index}
hostname {hn}
interface Port-channel1
 switchport mode trunk
! Port-channel created without member interfaces
end
"""


# =============================================================================
# 2. Cisco NX-OS Switch (Nexus)
# =============================================================================
class CiscoNXOSSwitchGenerator(ConfigGenerator):
    vendor = "Cisco"
    platform = "NX-OS"
    model = "9300"
    device_class = "switch"
    network_role = "datacenter_leaf"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'VPC', 'LACP', 'STP']
    product = "Nexus 9300 Switch"
    os_name = "Cisco NX-OS"
    os_version = "10.2"
    device_type = "switch"
    category = "switch"
    config_format = "cisco_nxos_cli"
    vendor_dir_name = "cisco_nxos_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""! GAACA Dataset — Cisco NX-OS Switch — SECURE — Sample {index}
version 10.2(3)
hostname {hn}
feature lacp
feature vpc
feature lldp
no feature telnet
no feature http-server
!
spanning-tree mode mst
spanning-tree port type edge bpduguard default
!
vlan {vlan}
  name Leaf-VLAN
!
interface Ethernet1/1
  switchport mode access
  switchport access vlan {vlan}
  spanning-tree port type edge
  storm-control broadcast level 5.0
  no shutdown
!
interface Ethernet1/48
  switchport mode trunk
  switchport trunk allowed vlan {vlan}
  no shutdown
!
username admin role network-admin password 5 {pwd}
logging server {syslog} 6
ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco NX-OS Switch — MISCONFIGURED — Sample {index}
hostname {hn}
feature telnet
feature http-server
username admin role network-admin password 0 admin
snmp-server community public ro
snmp-server community private rw
interface Ethernet1/1
  switchport
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco NX-OS Switch — EDGE CASE — Sample {index}
hostname {hn}
vpc domain 10
  ! Empty VPC domain without peer-keepalive destination
"""


# =============================================================================
# 3. Juniper Junos Switch (EX Series)
# =============================================================================
class JuniperJunosSwitchGenerator(ConfigGenerator):
    vendor = "Juniper Networks"
    platform = "Junos"
    model = "EX4300"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'RSTP', 'STORM_CONTROL', 'DHCP_SECURITY']
    product = "EX4300 / EX4400 Switch"
    os_name = "Junos OS"
    os_version = "21.x"
    device_type = "switch"
    category = "switch"
    config_format = "junos_hierarchy"
    vendor_dir_name = "juniper_junos_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""/* GAACA Dataset — Juniper EX Switch — SECURE — Sample {index} */
system {{
    host-name {hn};
    root-authentication {{
        encrypted-password "{pwd}";
    }}
    services {{
        ssh {{
            protocol-version v2;
        }}
    }}
    syslog {{
        host {syslog} {{
            any notice;
        }}
    }}
    ntp {{
        server {ntp};
    }}
}}
interfaces {{
    ge-0/0/0 {{
        unit 0 {{
            family ethernet-switching {{
                interface-mode access;
                vlan {{
                    members {vlan};
                }}
                storm-control default;
            }}
        }}
    }}
}}
forwarding-options {{
    storm-control-profiles default {{
        all {{
            bandwidth-percentage 20;
        }}
    }}
    dhcp-security {{
        group access-ports {{
            interface ge-0/0/0.0;
        }}
        group trusted-uplinks {{
            overrides {{
                trusted;
            }}
            interface ge-0/0/23.0;
        }}
    }}
}}
protocols {{
    rstp {{
        bpdu-block-on-edge;
        interface ge-0/0/0 {{
            edge;
        }}
    }}
}}
vlans {{
    vlan-{vlan} {{
        vlan-id {vlan};
    }}
}}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""/* GAACA Dataset — Juniper EX Switch — MISCONFIGURED — Sample {index} */
system {{
    host-name {hn};
    root-authentication {{
        plain-text-password-value "juniper123";
    }}
    services {{
        telnet;
        web-management {{
            http;
        }}
    }}
}}
interfaces {{
    ge-0/0/0 {{
        unit 0 {{
            family ethernet-switching;
        }}
    }}
}}
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""/* GAACA Dataset — Juniper EX Switch — EDGE CASE — Sample {index} */
system {{
    host-name {hn};
}}
protocols {{
    igmp-snooping {{
        vlan all {{
            /* Snooping on all without querier */
        }}
    }}
}}
"""


# =============================================================================
# 4. Arista EOS Switch
# =============================================================================
class AristaEOSSwitchGenerator(ConfigGenerator):
    vendor = "Arista Networks"
    platform = "EOS"
    model = "7050SX"
    device_class = "switch"
    network_role = "datacenter_leaf"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'MSTP', 'STORM_CONTROL']
    product = "7050SX / 7280 Switch"
    os_name = "EOS"
    os_version = "4.30"
    device_type = "switch"
    category = "switch"
    config_format = "arista_eos_cli"
    vendor_dir_name = "arista_eos_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""! GAACA Dataset — Arista EOS Switch — SECURE — Sample {index}
hostname {hn}
spanning-tree mode mstp
spanning-tree edge-port bpduguard default
!
vlan {vlan}
 name UserVlan
!
interface Ethernet1
 switchport mode access
 switchport access vlan {vlan}
 spanning-tree portfast
 storm-control broadcast level 10
 storm-control action trap
!
interface Ethernet48
 switchport mode trunk
!
management ssh
 protocol-version 2
 idle-timeout 10
!
no management api http-commands
username admin privilege 15 secret sha512 {pwd}
logging host {syslog}
ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Arista EOS Switch — MISCONFIGURED — Sample {index}
hostname {hn}
no spanning-tree edge-port bpduguard default
management telnet
 no shutdown
username admin privilege 15 secret 0 admin
snmp-server community public ro
snmp-server community private rw
interface Ethernet1
 switchport
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Arista EOS Switch — EDGE CASE — Sample {index}
hostname {hn}
interface Vxlan1
 ! Vxlan tunnel interface without source-interface or VNI mapping
"""


# =============================================================================
# 5. Huawei VRP Switch (CloudEngine / Quidway)
# =============================================================================
class HuaweiVRPSwitchGenerator(ConfigGenerator):
    vendor = "Huawei"
    platform = "VRP"
    model = "S5700"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'STP', 'PORT_SECURITY', 'DHCP_SNOOPING']
    product = "CloudEngine S5700 / S6700"
    os_name = "VRP"
    os_version = "V800R021"
    device_type = "switch"
    category = "switch"
    config_format = "huawei_vrp_cli"
    vendor_dir_name = "huawei_vrp_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""# GAACA Dataset — Huawei VRP Switch — SECURE — Sample {index}
sysname {hn}
#
stp mode rstp
stp bpdu-protection
#
dhcp enable
dhcp snooping enable
#
vlan {vlan}
 description Workstation-VLAN
#
interface GigabitEthernet0/0/1
 port link-type access
 port default vlan {vlan}
 stp edged-port enable
 port-security enable
 port-security max-mac-num 2
 port-security protect-action shutdown
 dhcp snooping check dhcp-chaddr enable
#
undo telnet server enable
stelnet server enable
#
local-user admin password irreversible-cipher {pwd}
local-user admin service-type stelnet
local-user admin level 15
#
info-center loghost {syslog}
ntp-service unicast-server {ntp}
#
return
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Huawei VRP Switch — MISCONFIGURED — Sample {index}
sysname {hn}
#
telnet server enable
undo stp bpdu-protection
#
local-user admin password simple huawei123
local-user admin service-type telnet
#
snmp-agent community read public
snmp-agent community write private
#
interface GigabitEthernet0/0/1
 port link-type access
#
return
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Huawei VRP Switch — EDGE CASE — Sample {index}
sysname {hn}
#
interface Eth-Trunk1
 ! Empty trunk without member ports
#
return
"""


# =============================================================================
# 6. Aruba AOS-CX Switch
# =============================================================================
class ArubaAOSCXSwitchGenerator(ConfigGenerator):
    vendor = "Aruba / HPE"
    platform = "AOS-CX"
    model = "6200"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'LOOP_PROTECT', 'BPDU_GUARD', 'STP']
    product = "CX 6200 / 6300 Switch"
    os_name = "AOS-CX"
    os_version = "10.12"
    device_type = "switch"
    category = "switch"
    config_format = "aruba_aoscx_cli"
    vendor_dir_name = "aruba_aoscx_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""! GAACA Dataset — Aruba AOS-CX Switch — SECURE — Sample {index}
hostname {hn}
spanning-tree
spanning-tree bpdu-guard
spanning-tree port-type admin-edge
vlan {vlan}
    name Client-VLAN
interface 1/1/1
    no shutdown
    vlan access {vlan}
    loop-protect
    spanning-tree bpdu-guard
interface 1/1/24
    no shutdown
    vlan trunk allowed {vlan}
user admin group administrators password ciphertext {pwd}
no telnet-server
ssh server vrf default
logging {syslog} severity info
ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Aruba AOS-CX Switch — MISCONFIGURED — Sample {index}
hostname {hn}
no spanning-tree bpdu-guard
telnet-server
user admin group administrators password plaintext admin
snmp-server community public
snmp-server community private rw
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Aruba AOS-CX Switch — EDGE CASE — Sample {index}
hostname {hn}
port-access role UNASSIGNED
    ! Role defined without ACL or auth method
"""


# =============================================================================
# 7. Extreme EXOS Switch
# =============================================================================
class ExtremeEXOSSwitchGenerator(ConfigGenerator):
    vendor = "Extreme Networks"
    platform = "EXOS"
    model = "X440"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'STP', 'ELRP']
    product = "Summit X440 / X460 Switch"
    os_name = "EXOS"
    os_version = "31.x"
    device_type = "switch"
    category = "switch"
    config_format = "extreme_exos_cli"
    vendor_dir_name = "extreme_exos_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""# GAACA Dataset — Extreme EXOS Switch — SECURE — Sample {index}
configure snmp sysName "{hn}"
disable telnet
enable ssh2
configure account admin encrypted "{pwd}"
create vlan "ClientVlan"
configure vlan "ClientVlan" tag {vlan}
configure vlan "ClientVlan" add ports 1:1 untagged
enable stpd s0
configure stpd s0 ports edge 1:1
configure stpd s0 ports bpdu-restrict 1:1 enable
enable elrp-client
configure elrp-client periodic "ClientVlan" ports 1:1 interval 1 log and-trap
configure syslog add {syslog}:514 vr VR-Default local0 notice
configure sntp-client add server {ntp} vr VR-Default
enable sntp-client
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Extreme EXOS Switch — MISCONFIGURED — Sample {index}
configure snmp sysName "{hn}"
enable telnet
disable ssh2
configure account admin password "admin"
configure snmp add community readonly "public"
configure snmp add community readwrite "private"
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Extreme EXOS Switch — EDGE CASE — Sample {index}
configure snmp sysName "{hn}"
enable netlogin dot1x
! Netlogin enabled but ports not assigned
"""


# =============================================================================
# 8. Nokia SR OS Switch (7210 SAS)
# =============================================================================
class NokiaSROSSwitchGenerator(ConfigGenerator):
    vendor = "Nokia"
    platform = "SR OS"
    model = "7210 SAS"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VPLS', 'QOS']
    product = "7210 SAS Ethernet Switch"
    os_name = "SR OS"
    os_version = "22.x"
    device_type = "switch"
    category = "switch"
    config_format = "nokia_sros_cli"
    vendor_dir_name = "nokia_sros_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""# GAACA Dataset — Nokia SAS Switch — SECURE — Sample {index}
configure system name "{hn}"
configure system security telnet-server shutdown
configure system security ssh server-shutdown no
configure system security user "admin" password "{pwd}"
configure service
    vpls {vlan} customer 1 create
        stp
            shutdown
        exit
        sap 1/1/1 create
            ingress
                qos 1
            exit
            no shutdown
        exit
        no shutdown
    exit
exit
configure log syslog {syslog} facility local7
configure system ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Nokia SAS Switch — MISCONFIGURED — Sample {index}
configure system name "{hn}"
configure system security telnet-server no shutdown
configure system security ssh server-shutdown
configure system security user "admin" password "admin"
configure system security snmp community "public" r
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Nokia SAS Switch — EDGE CASE — Sample {index}
configure system name "{hn}"
configure service
    vpls 999 customer 1 create
        ! Empty VPLS without SAP or SDP bindings
    exit
exit
"""


# =============================================================================
# 9. Dell OS10 Switch
# =============================================================================
class DellOS10SwitchGenerator(ConfigGenerator):
    vendor = "Dell Technologies"
    platform = "OS10"
    model = "PowerSwitch S-Series"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'RSTP', 'STORM_CONTROL']
    product = "PowerSwitch S-Series"
    os_name = "OS10 Enterprise"
    os_version = "10.5.x"
    device_type = "switch"
    category = "switch"
    config_format = "dell_os10_cli"
    vendor_dir_name = "dell_os10_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""! GAACA Dataset — Dell OS10 Switch — SECURE — Sample {index}
hostname {hn}
no ip telnet server enable
ip ssh server enable
username admin password {pwd} role sysadmin
spanning-tree mode rstp
spanning-tree rstp bpduguard enable
interface vlan {vlan}
 description Access-Data
 no shutdown
interface ethernet1/1/1
 switchport mode access
 switchport access vlan {vlan}
 spanning-tree port-type edge
 storm-control broadcast 1000
 no shutdown
logging server {syslog}
ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Dell OS10 Switch — MISCONFIGURED — Sample {index}
hostname {hn}
ip telnet server enable
no ip ssh server enable
username admin password admin role sysadmin
snmp-server community public ro
snmp-server community private rw
interface ethernet1/1/1
 switchport mode access
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Dell OS10 Switch — EDGE CASE — Sample {index}
hostname {hn}
interface port-channel10
 ! Port channel defined without physical member ports
"""


# =============================================================================
# 10. MikroTik RouterOS Switch (CRS Series)
# =============================================================================
class MikroTikRouterOSSwitchGenerator(ConfigGenerator):
    vendor = "MikroTik"
    platform = "RouterOS"
    model = "CRS326"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['BRIDGE_VLAN', 'RSTP']
    product = "Cloud Router Switch (CRS)"
    os_name = "RouterOS"
    os_version = "v7.x"
    device_type = "switch"
    category = "switch"
    config_format = "mikrotik_rsc"
    vendor_dir_name = "mikrotik_routeros_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""# GAACA Dataset — MikroTik CRS Switch — SECURE — Sample {index}
/system identity set name="{hn}"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set ssh disabled=no strong-crypto=yes
/user set admin password="{pwd}" group=full
/interface bridge add name=bridge1 vlan-filtering=yes protocol-mode=rstp
/interface bridge port add bridge=bridge1 interface=ether1 edge=yes bpdu-guard=yes
/interface bridge vlan add bridge=bridge1 tagged=sfp-sfpplus1 untagged=ether1 vlan-ids={vlan}
/system logging action add name=rem target=remote remote={syslog}
/system logging add topics=system,info action=rem
/system ntp client set enabled=yes
/system ntp client servers add address={ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — MikroTik CRS Switch — MISCONFIGURED — Sample {index}
/system identity set name="{hn}"
/ip service set telnet disabled=no
/ip service set www disabled=no
/user set admin password="" group=full
/interface bridge add name=bridge1 vlan-filtering=no
/snmp set enabled=yes
/snmp community set [ find default=yes ] name=public write-access=yes
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — MikroTik CRS Switch — EDGE CASE — Sample {index}
/system identity set name="{hn}"
/interface ethernet switch rule add switch=switch1
! Switch rule with no match conditions or actions
"""


# =============================================================================
# 11. TP-Link Omada Managed Switch
# =============================================================================
class TPLinkOmadaSwitchGenerator(ConfigGenerator):
    vendor = "TP-Link"
    platform = "Omada OS"
    model = "SG3428"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'STP', 'PORT_SECURITY', 'DHCP_SNOOPING']
    product = "Omada SG3428 / SG3452"
    os_name = "Omada OS"
    os_version = "v5"
    device_type = "switch"
    category = "switch"
    config_format = "cisco_ios_cli"
    vendor_dir_name = "tplink_omada"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""# GAACA Dataset — TP-Link Omada Switch — SECURE — Sample {index}
hostname "{hn}"
user name admin password {pwd} privilege 15
no service telnet
service ssh
spanning-tree
spanning-tree bpdu-guard
vlan {vlan}
 name "Client_LAN"
interface gigabitEthernet 1/0/1
 switchport mode access
 switchport access vlan {vlan}
 port-security
 port-security max-mac 2
ip dhcp snooping
ip dhcp snooping vlan {vlan}
logging host {syslog}
sntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — TP-Link Omada Switch — MISCONFIGURED — Sample {index}
hostname "{hn}"
user name admin password admin privilege 15
service telnet
no service ssh
snmp-server community public ro
snmp-server community private rw
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — TP-Link Omada Switch — EDGE CASE — Sample {index}
hostname "{hn}"
vlan 4000
! VLAN with no members assigned
"""


# =============================================================================
# 12. D-Link Managed Switch
# =============================================================================
class DLinkManagedSwitchGenerator(ConfigGenerator):
    vendor = "D-Link"
    platform = "D-Link OS"
    model = "DGS-3130"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['LOOP_DETECT', 'DHCP_SNOOPING']
    product = "DGS-3130 / DGS-3630"
    os_name = "D-Link OS"
    os_version = "v4.x"
    device_type = "switch"
    category = "switch"
    config_format = "dlink_cli"
    vendor_dir_name = "dlink_managed"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — D-Link Managed Switch — SECURE — Sample {index}
config snmp system_name "{hn}"
disable telnet
enable ssh
config admin admin password {pwd}
enable bpdu_protection
enable loopdetect
config loopdetect trap enable
enable dhcp_snooping
config sntp server primary {ntp}
enable sntp
create log_host {syslog} severity notice
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — D-Link Managed Switch — MISCONFIGURED — Sample {index}
config snmp system_name "{hn}"
enable telnet
disable ssh
config admin admin password admin
create snmp community public view restricted read_only
create snmp community private view restricted read_write
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — D-Link Managed Switch — EDGE CASE — Sample {index}
config snmp system_name "{hn}"
create link_aggregation group_id 1
! Link aggregation group without ports
"""


# =============================================================================
# 13. Netgear Managed Switch
# =============================================================================
class NetgearManagedSwitchGenerator(ConfigGenerator):
    vendor = "Netgear"
    platform = "FASTPATH"
    model = "M4300"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['PORT_SECURITY', 'STP']
    product = "ProSAFE M4300 / M4500"
    os_name = "FASTPATH"
    os_version = "12.x"
    device_type = "switch"
    category = "switch"
    config_format = "cisco_ios_cli"
    vendor_dir_name = "netgear_managed"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Netgear Managed Switch — SECURE — Sample {index}
hostname "{hn}"
ip ssh server enable
no ip telnet server enable
username "admin" password {pwd} level 15
spanning-tree
spanning-tree bpduguard
interface 1/0/1
 set port-security
 set port-security max-mac 1
logging host {syslog}
sntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Netgear Managed Switch — MISCONFIGURED — Sample {index}
hostname "{hn}"
ip telnet server enable
no ip ssh server enable
username "admin" password "password" level 15
snmp-server community "public" ro
snmp-server community "private" rw
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Netgear Managed Switch — EDGE CASE — Sample {index}
hostname "{hn}"
interface lag 1
! LAG defined with no physical member interfaces
"""


# =============================================================================
# 14. Ruijie RGOS Switch
# =============================================================================
class RuijieRGOSSwitchGenerator(ConfigGenerator):
    vendor = "Ruijie Networks"
    platform = "RGOS"
    model = "RG-S2910"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'PORT_SECURITY', 'STP']
    product = "RG-S Series Managed Switch"
    os_name = "RGOS"
    os_version = "11.x"
    device_type = "switch"
    category = "switch"
    config_format = "ruijie_rgos_cli"
    vendor_dir_name = "ruijie_rgos_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""! GAACA Dataset — Ruijie Switch — SECURE — Sample {index}
hostname {hn}
service password-encryption
enable secret {pwd}
no telnet-server enable
ssh-server enable
spanning-tree
spanning-tree bpduguard default
vlan {vlan}
interface GigabitEthernet 0/1
 switchport mode access
 switchport access vlan {vlan}
 switchport port-security
 switchport port-security violation shutdown
logging server {syslog}
ntp server {ntp}
line vty 0 4
 transport input ssh
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruijie Switch — MISCONFIGURED — Sample {index}
hostname {hn}
telnet-server enable
no ssh-server enable
enable password ruijie
snmp-server community public ro
snmp-server community private rw
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruijie Switch — EDGE CASE — Sample {index}
hostname {hn}
interface AggregatePort 1
 ! Empty aggregation port
"""


# =============================================================================
# 15. H3C Comware Switch
# =============================================================================
class H3CComwareSwitchGenerator(ConfigGenerator):
    vendor = "H3C"
    platform = "Comware"
    model = "S5130"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'STP', 'PORT_SECURITY']
    product = "S5130 / S5560 Switch"
    os_name = "Comware"
    os_version = "v7"
    device_type = "switch"
    category = "switch"
    config_format = "h3c_comware_cli"
    vendor_dir_name = "h3c_comware_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""# GAACA Dataset — H3C Comware Switch — SECURE — Sample {index}
sysname {hn}
stp mode rstp
stp bpdu-protection
undo telnet server enable
ssh server enable
local-user admin class manage
 password cipher {pwd}
 service-type stelnet
 authorization-attribute user-role network-admin
vlan {vlan}
interface GigabitEthernet1/0/1
 port link-type access
 port default vlan {vlan}
 stp edged-port enable
 port-security enable
info-center loghost {syslog}
ntp-service unicast-server {ntp}
return
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — H3C Comware Switch — MISCONFIGURED — Sample {index}
sysname {hn}
telnet server enable
undo stp bpdu-protection
local-user admin class manage
 password simple admin
 service-type telnet
snmp-agent community read public
snmp-agent community write private
return
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — H3C Comware Switch — EDGE CASE — Sample {index}
sysname {hn}
interface Bridge-Aggregation1
 ! Empty aggregation group
return
"""


# =============================================================================
# 16. Allied Telesis AlliedWare Plus Switch
# =============================================================================
class AlliedTelesisAWSwitchGenerator(ConfigGenerator):
    vendor = "Allied Telesis"
    platform = "AlliedWare Plus"
    model = "x530"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'RSTP', 'MAC_AUTH']
    product = "x530 / x930 Series Switch"
    os_name = "AlliedWare Plus"
    os_version = "5.5.x"
    device_type = "switch"
    category = "switch"
    config_format = "allied_telesis_cli"
    vendor_dir_name = "allied_telesis_aw_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Allied Telesis Switch — SECURE — Sample {index}
service password-encryption
hostname {hn}
no service telnet
service ssh
username admin privilege 15 password 8 {pwd}
spanning-tree mode rstp
spanning-tree edge-port bpdu-guard
interface port1.0.1
 switchport mode access
 spanning-tree edge-port
 auth-mac
log host {syslog}
ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Allied Telesis Switch — MISCONFIGURED — Sample {index}
hostname {hn}
service telnet
no service ssh
username admin privilege 15 password 0 admin
snmp-server community public ro
snmp-server community private rw
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Allied Telesis Switch — EDGE CASE — Sample {index}
hostname {hn}
interface static-channel-group 1
 ! Channel group with no ports
"""


# =============================================================================
# 17. SONiC Network OS Switch
# =============================================================================
class SONiCConfigDBSwitchGenerator(ConfigGenerator):
    vendor = "Open Source / Linux Foundation"
    platform = "SONiC"
    model = "AS7726"
    device_class = "switch"
    network_role = "datacenter_leaf"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'STP']
    product = "SONiC Leaf/Spine Switch"
    os_name = "SONiC"
    os_version = "202311"
    device_type = "switch"
    category = "switch"
    config_format = "sonic_config_db_json"
    vendor_dir_name = "sonic_configdb_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        cfg = {
            "DEVICE_METADATA": {
                "localhost": {
                    "hostname": hn,
                    "hwsku": "Accton-AS7726-32X",
                    "type": "LeafSwitch"
                }
            },
            "VLAN": {
                f"Vlan{vlan}": {
                    "vlanid": str(vlan)
                }
            },
            "VLAN_MEMBER": {
                f"Vlan{vlan}|Ethernet0": {
                    "tagging_mode": "untagged"
                }
            },
            "STP": {
                "GLOBAL": {
                    "status": "enabled",
                    "mode": "rapid_pvst",
                    "bpdu_guard": "enabled"
                }
            },
            "NTP_SERVER": {ntp: {}},
            "SYSLOG_SERVER": {syslog: {"port": "514"}}
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "DEVICE_METADATA": {
                "localhost": {
                    "hostname": hn,
                    "type": "LeafSwitch"
                }
            },
            "STP": {
                "GLOBAL": {
                    "status": "disabled",
                    "bpdu_guard": "disabled"
                }
            },
            "SNMP_COMMUNITY": {
                "public": {"type": "ro"},
                "private": {"type": "rw"}
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "DEVICE_METADATA": {
                "localhost": {
                    "hostname": hn
                }
            },
            "VLAN": {
                "Vlan4090": {}
            }
        }
        return json.dumps(cfg, indent=4)


# =============================================================================
# 18. Brocade FastIron Switch
# =============================================================================
class BrocadeFastIronSwitchGenerator(ConfigGenerator):
    vendor = "Brocade / Ruckus"
    platform = "FastIron"
    model = "ICX 6450"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'STP']
    product = "ICX 6450 / 6610 Switch"
    os_name = "FastIron"
    os_version = "08.0.95"
    device_type = "switch"
    category = "switch"
    config_format = "brocade_cli"
    vendor_dir_name = "brocade_fastiron_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""! GAACA Dataset — Brocade FastIron Switch — SECURE — Sample {index}
ver 08.0.95
hostname {hn}
enable super-user-password 8 {pwd}
no telnet server
ip ssh server
vlan {vlan} name Data by port
 untagged ethe 1/1/1
 spanning-tree 802-1w
 stp-bpdu-guard
logging host {syslog}
sntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Brocade FastIron Switch — MISCONFIGURED — Sample {index}
hostname {hn}
enable super-user-password 0 brocade
telnet server
no ip ssh server
snmp-server community public ro
snmp-server community private rw
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Brocade FastIron Switch — EDGE CASE — Sample {index}
hostname {hn}
vlan 100
 ! empty vlan with no ports
"""


# =============================================================================
# 19. Ruckus ICX Switch
# =============================================================================
class RuckusICXSwitchGenerator(ConfigGenerator):
    vendor = "Ruckus Networks"
    platform = "FastIron"
    model = "ICX 7150"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'RSTP']
    product = "ICX 7150 / 7450 Switch"
    os_name = "FastIron"
    os_version = "08.0.95"
    device_type = "switch"
    category = "switch"
    config_format = "brocade_cli"
    vendor_dir_name = "ruckus_icx"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""! GAACA Dataset — Ruckus ICX Switch — SECURE — Sample {index}
hostname {hn}
no telnet server
ip ssh server
username admin privilege 0 password 8 {pwd}
vlan {vlan}
 untagged ethe 1/1/1
 spanning-tree rstp
 spanning-tree bpdu-guard
logging host {syslog}
sntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruckus ICX Switch — MISCONFIGURED — Sample {index}
hostname {hn}
telnet server
no ip ssh server
username admin password 0 admin
snmp-server community public ro
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruckus ICX Switch — EDGE CASE — Sample {index}
hostname {hn}
lag "UPLINK" static
 ! LAG with no ports
"""


# =============================================================================
# 20. Ubiquiti UniFi Switch
# =============================================================================
class UbiquitiUniFiSwitchGenerator(ConfigGenerator):
    vendor = "Ubiquiti Networks"
    platform = "UniFi OS"
    model = "USW-Pro"
    device_class = "switch"
    network_role = "access"
    routing_capability = True
    l3_capable = True
    capabilities = ['VLAN', 'RSTP', 'PORT_ISOLATION']
    product = "UniFi Switch USW-Pro"
    os_name = "UniFi OS"
    os_version = "6.x"
    device_type = "switch"
    category = "switch"
    config_format = "ini"
    vendor_dir_name = "ubiquiti_unifi_sw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        vlan = self.rand_vlan()
        return f"""# GAACA Dataset — Ubiquiti UniFi Switch — SECURE — Sample {index}
system.hostname={hn}
system.root_pwd={pwd}
sshd.status=enabled
sshd.port=22
telnetd.status=disabled
switch.stp.status=enabled
switch.stp.version=rstp
switch.stp.bpduguard=enabled
switch.dhcp_snooping.status=enabled
switch.vlan.1.name=ClientData
switch.vlan.1.vid={vlan}
switch.port.1.mode=access
switch.port.1.pvid={vlan}
switch.port.1.isolate=enabled
switch.port.1.storm_control.broadcast_rate=100
syslog.status=enabled
syslog.remote_ip={syslog}
ntp.status=enabled
ntp.server={ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Ubiquiti UniFi Switch — MISCONFIGURED — Sample {index}
system.hostname={hn}
system.root_pwd=ubnt
sshd.status=disabled
telnetd.status=enabled
switch.stp.status=disabled
switch.stp.bpduguard=disabled
switch.dhcp_snooping.status=disabled
snmp.status=enabled
snmp.community=public
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Ubiquiti UniFi Switch — EDGE CASE — Sample {index}
system.hostname={hn}
switch.mirror.source=1
switch.mirror.dest=0
"""


# =============================================================================
# Registry of all switch generators
# =============================================================================
SWITCH_GENERATORS = [
    CiscoIOSSwitchGenerator,
    CiscoNXOSSwitchGenerator,
    JuniperJunosSwitchGenerator,
    AristaEOSSwitchGenerator,
    HuaweiVRPSwitchGenerator,
    ArubaAOSCXSwitchGenerator,
    ExtremeEXOSSwitchGenerator,
    NokiaSROSSwitchGenerator,
    DellOS10SwitchGenerator,
    MikroTikRouterOSSwitchGenerator,
    TPLinkOmadaSwitchGenerator,
    DLinkManagedSwitchGenerator,
    NetgearManagedSwitchGenerator,
    RuijieRGOSSwitchGenerator,
    H3CComwareSwitchGenerator,
    AlliedTelesisAWSwitchGenerator,
    SONiCConfigDBSwitchGenerator,
    BrocadeFastIronSwitchGenerator,
    RuckusICXSwitchGenerator,
    UbiquitiUniFiSwitchGenerator,
]
