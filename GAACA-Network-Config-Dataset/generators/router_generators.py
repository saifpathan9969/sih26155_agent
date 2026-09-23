"""
GAACA Dataset — Router Configuration Generators
=================================================
20 vendor generators for enterprise & service provider router configurations.
Each produces secure, misconfigured, and edge_case variants.
"""

from __future__ import annotations
import json
from generators.base import ConfigGenerator


# =============================================================================
# 1. Cisco IOS
# =============================================================================
class CiscoIOSGenerator(ConfigGenerator):
    vendor = "Cisco"
    platform = "IOS"
    model = "ISR 4451"
    device_class = "router"
    network_role = "wan"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'AAA', 'ACL']
    product = "IOS Router"
    os_name = "Cisco IOS"
    os_version = "15.x"
    device_type = "router"
    category = "router"
    config_format = "cisco_ios_cli"
    vendor_dir_name = "cisco_ios"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        radius = self.rand_radius()
        psk = self.rand_psk()
        asn = self.rand_as_number()
        return f"""! GAACA Dataset — Cisco IOS — SECURE — Sample {index}
!
version 15.7
service timestamps debug datetime msec localtime show-timezone
service timestamps log datetime msec localtime show-timezone
service password-encryption
service sequence-numbers
no service dhcp
no service finger
no service pad
no service udp-small-servers
no service tcp-small-servers
!
hostname {hn}
!
boot-start-marker
boot-end-marker
!
security passwords min-length 12
security authentication failure rate 3 logs
!
aaa new-model
aaa authentication login default group radius local
aaa authentication enable default group radius enable
aaa authorization exec default group radius local
aaa accounting exec default start-stop group radius
aaa accounting commands 15 default start-stop group radius
!
radius server RADIUS-AUTH
 address ipv4 {radius} auth-port 1812 acct-port 1813
 key {psk}
!
ip domain name example.lab
crypto key generate rsa modulus 4096
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3
ip ssh server algorithm encryption aes256-gcm aes128-gcm aes256-ctr
ip ssh server algorithm mac hmac-sha2-512 hmac-sha2-256
!
no ip http server
ip http secure-server
ip http secure-ciphersuite high
!
username admin privilege 15 secret {pwd}
enable secret {pwd}
!
interface GigabitEthernet0/0/0
 description WAN-Primary-Uplink
 ip address {self.rand_ip()} 255.255.255.252
 no ip redirects
 no ip proxy-arp
 no ip unreachables
 no ip directed-broadcast
 ip verify unicast source reachable-via rx
 ip access-group WAN-INGRESS in
 no shutdown
!
interface GigabitEthernet0/0/1
 description LAN-Internal
 ip address {self.rand_ip()} 255.255.255.0
 no ip redirects
 no ip proxy-arp
 no shutdown
!
router bgp {asn}
 bgp log-neighbor-changes
 neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
 neighbor {self.rand_ip()} password {psk}
 neighbor {self.rand_ip()} prefix-list BGP-IN in
 neighbor {self.rand_ip()} prefix-list BGP-OUT out
!
ip access-list extended WAN-INGRESS
 permit tcp {self.rand_ip()} 0.0.0.255 host {self.rand_ip()} eq 22
 permit esp any host {self.rand_ip()}
 permit udp any host {self.rand_ip()} eq 500
 permit udp any host {self.rand_ip()} eq 4500
 deny ip any any log-input
!
ip access-list standard MGMT-ACL
 permit {self.rand_ip()} 0.0.0.255
 deny any log
!
ip prefix-list BGP-IN seq 10 permit 192.0.2.0/24
ip prefix-list BGP-IN seq 20 deny 0.0.0.0/0 le 32
!
ip prefix-list BGP-OUT seq 10 permit 198.51.100.0/24
ip prefix-list BGP-OUT seq 20 deny 0.0.0.0/0 le 32
!
logging buffered 64000 informational
logging host {syslog} transport udp port 514
logging source-interface GigabitEthernet0/0/1
!
snmp-server group SNMPv3Group v3 priv
snmp-server user snmpv3user SNMPv3Group v3 auth sha {pwd} priv aes 256 {pwd}
snmp-server host {syslog} version 3 priv snmpv3user
no snmp-server community public
no snmp-server community private
!
ntp authenticate
ntp authentication-key 1 md5 {psk}
ntp trusted-key 1
ntp server {ntp} key 1 prefer
!
banner motd ^C
UNAUTHORIZED ACCESS TO THIS DEVICE IS STRICTLY PROHIBITED.
ALL SESSIONS ARE MONITORED, LOGGED, AND AUDITED.
^C
!
line con 0
 exec-timeout 5 0
 login authentication default
 transport output none
line aux 0
 no exec
 transport input none
line vty 0 4
 exec-timeout 5 0
 access-class MGMT-ACL in
 login authentication default
 transport input ssh
 transport output none
!
end
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco IOS — MISCONFIGURED — Sample {index}
!
version 15.1
service timestamps debug uptime
service timestamps log uptime
no service password-encryption
!
hostname {hn}
!
enable password cisco
enable secret cisco
username admin privilege 15 password admin
!
interface GigabitEthernet0/0/0
 ip address {self.rand_ip()} 255.255.255.0
 ip redirects
 ip proxy-arp
 no shutdown
!
interface GigabitEthernet0/0/1
 ip address {self.rand_ip()} 255.255.255.0
 no shutdown
!
router bgp {self.rand_as_number()}
 neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
!
ip http server
no ip http secure-server
!
snmp-server community public RW
snmp-server community private RW
snmp-server host {self.rand_ip()} public
!
no logging buffered
no logging console
!
no ntp server
!
line con 0
 password cisco
 login
line vty 0 4
 password cisco
 login
 transport input telnet
!
end
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco IOS — EDGE CASE — Sample {index}
! Partial configuration with mixed old-style ACL and missing routing block
hostname {hn}
ip domain name old.lab
!
access-list 1 permit any
access-list 100 permit ip any any
!
interface FastEthernet0/0
 ip address {self.rand_ip()} 255.255.255.0
 ip access-group 100 in
!
router rip
 version 1
 network 192.0.2.0
!
line vty 0 4
 access-class 1 in
 transport input all
!
end
"""


# =============================================================================
# 2. Cisco IOS-XE
# =============================================================================
class CiscoIOSXEGenerator(ConfigGenerator):
    vendor = "Cisco"
    platform = "IOS-XE"
    model = "Catalyst 8300"
    device_class = "router"
    network_role = "wan"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['OSPF']
    capabilities = ['OSPF', 'VRF']
    product = "Catalyst 8000 / ISR 4000"
    os_name = "Cisco IOS-XE"
    os_version = "17.x"
    device_type = "router"
    category = "router"
    config_format = "cisco_iosxe_cli"
    vendor_dir_name = "cisco_iosxe"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        radius = self.rand_radius()
        psk = self.rand_psk()
        return f"""! GAACA Dataset — Cisco IOS-XE — SECURE — Sample {index}
version 17.9
service timestamps debug datetime msec localtime show-timezone
service timestamps log datetime msec localtime show-timezone
service password-encryption
service call-home
platform punt-keepalive disable-kernel-core
!
hostname {hn}
!
vrf definition Mgmt-intf
 address-family ipv4
 exit-address-family
!
aaa new-model
aaa group server radius RADIUS-GROUP
 server name RAD-1
!
radius server RAD-1
 address ipv4 {radius} auth-port 1812 acct-port 1813
 key {psk}
!
aaa authentication login default group RADIUS-GROUP local
aaa authorization exec default group RADIUS-GROUP local
aaa accounting exec default start-stop group RADIUS-GROUP
!
ip domain name enterprise.net
ip ssh version 2
ip ssh time-out 30
ip ssh authentication-retries 2
ip ssh client algorithm encryption aes256-gcm
ip ssh server algorithm encryption aes256-gcm aes256-ctr
!
no ip http server
ip http secure-server
ip http secure-active-session-modules none
ip http secure-trustpoint CISCO_IDEVID_SUDI
!
username secadmin privilege 15 algorithm-type scrypt secret {pwd}
enable algorithm-type scrypt secret {pwd}
!
interface GigabitEthernet0/0/0
 description WAN-Edge
 ip address {self.rand_ip()} 255.255.255.252
 ip verify unicast source reachable-via rx
 no ip proxy-arp
 no ip redirects
 no ip unreachables
 no shutdown
!
interface GigabitEthernet0
 vrf forwarding Mgmt-intf
 ip address {self.rand_ip()} 255.255.255.0
 no shutdown
!
router ospfv3 1
 router-id {self.rand_ip()}
 authentication ipsec spi 1000 sha1 {psk[:40]}
!
snmp-server group SECGROUP v3 priv read V1DEFAULT access 10
snmp-server user secuser SECGROUP v3 auth sha {pwd} priv aes 256 {pwd}
snmp-server host {syslog} vrf Mgmt-intf version 3 priv secuser
!
logging buffered 128000 informational
logging host {syslog} vrf Mgmt-intf
!
ntp server vrf Mgmt-intf {ntp} prefer
ntp authenticate
ntp trusted-key 1
!
line vty 0 4
 exec-timeout 10 0
 transport input ssh
 transport output none
!
end
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco IOS-XE — MISCONFIGURED — Sample {index}
version 17.3
hostname {hn}
!
username cisco privilege 15 password 0 cisco
enable password cisco
!
ip http server
no ip http secure-server
ip http authentication local
!
interface GigabitEthernet0/0/0
 ip address {self.rand_ip()} 255.255.255.0
 no shutdown
!
router ospf 1
 network 0.0.0.0 255.255.255.255 area 0
!
snmp-server community public RO
snmp-server community private RW
!
line vty 0 4
 password cisco
 login
 transport input all
!
end
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco IOS-XE — EDGE CASE — Sample {index}
! Conflicting AAA definitions with unreferenced trustpoint
hostname {hn}
crypto pki trustpoint UNKNOWN_TP
 enrollment terminal
!
aaa new-model
aaa authentication login default local
!
interface TenGigabitEthernet0/1/0
 description Trunk-Uplink
! Missing IP configuration
!
end
"""


# =============================================================================
# 3. Cisco NX-OS
# =============================================================================
class CiscoNXOSGenerator(ConfigGenerator):
    vendor = "Cisco"
    platform = "NX-OS"
    model = "Nexus 9300"
    device_class = "switch"
    network_role = "datacenter_spine"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'VRF', 'LACP', 'VLAN']
    product = "Nexus 9000 Router"
    os_name = "Cisco NX-OS"
    os_version = "10.x"
    device_type = "router"
    category = "router"
    config_format = "cisco_nxos_cli"
    vendor_dir_name = "cisco_nxos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Cisco NX-OS — SECURE — Sample {index}
version 10.3(1)
hostname {hn}
!
feature ssh
feature bgp
feature ospf
feature interface-vlan
feature tacacs+
!
no feature telnet
no feature http-server
!
service password-encryption
ssh key rsa 4096 force
ssh server key-exchange dh-group14-sha256,ecdh-sha2-nistp384
ssh server ciphers aes256-gcm,aes128-gcm
!
username admin role network-admin password 5 {pwd}
!
vrf context management
 ip route 0.0.0.0/0 {self.rand_ip()}
!
interface mgmt0
 vrf member management
 ip address {self.rand_ip()}/24
 no shutdown
!
interface Ethernet1/1
 description WAN-ROUTER-LINK
 no switchport
 ip address {self.rand_ip()}/30
 no ip redirects
 no ip directed-broadcast
 no shutdown
!
router bgp {self.rand_as_number()}
 router-id {self.rand_ip()}
 address-family ipv4 unicast
 neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
   password 7 {pwd}
   address-family ipv4 unicast
!
logging server {syslog} 6 use-vrf management
logging level bgp 5
logging level ospf 5
!
ntp server {ntp} use-vrf management prefer
!
line console
 exec-timeout 10
line vty
 exec-timeout 10
!
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco NX-OS — MISCONFIGURED — Sample {index}
version 10.1
hostname {hn}
!
feature telnet
feature http-server
!
username admin password 0 admin role network-admin
!
interface mgmt0
 ip address {self.rand_ip()}/24
 no shutdown
!
snmp-server community public ro
snmp-server community private rw
!
line vty
 no exec-timeout
!
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco NX-OS — EDGE CASE — Sample {index}
hostname {hn}
feature bgp
router bgp 65000
 ! empty bgp block without neighbors
interface Ethernet1/1
 ! unassigned interface in routed mode
 no switchport
!
"""


# =============================================================================
# 4. Cisco IOS-XR
# =============================================================================
class CiscoIOSXRGenerator(ConfigGenerator):
    vendor = "Cisco"
    platform = "IOS-XR"
    model = "ASR 9000"
    device_class = "router"
    network_role = "core"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'VRF', 'NETCONF']
    product = "ASR 9000 / 8000"
    os_name = "Cisco IOS-XR"
    os_version = "7.x"
    device_type = "router"
    category = "router"
    config_format = "cisco_iosxr_cli"
    vendor_dir_name = "cisco_iosxr"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Cisco IOS-XR — SECURE — Sample {index}
hostname {hn}
service timestamps log datetime msec
telnet vrf default ipv4 server max-servers 0
ssh server v2
ssh server netconf vrf default
ssh server algorithms key-exchange group14-sha256
ssh server algorithms cipher aes256-gcm
!
username netadmin
 group root-lr
 group cisco-support
 secret 10 {pwd}
!
vrf MGMT
 address-family ipv4 unicast
!
interface MgmtEth0/RP0/CPU0/0
 vrf MGMT
 ipv4 address {self.rand_ip()} 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/0/0/0
 description CORE-TRANSIT
 ipv4 address {self.rand_ip()} 255.255.255.252
 ipv4 verify unicast source reachable-via rx
 no shutdown
!
router bgp {self.rand_as_number()}
 bgp router-id {self.rand_ip()}
 address-family ipv4 unicast
 !
 neighbor {self.rand_ip()}
  remote-as {self.rand_as_number()}
  password clear {pwd}
  address-family ipv4 unicast
   route-policy PASS-ALL in
   route-policy PASS-ALL out
  !
 !
!
logging {syslog} vrf MGMT
ntp
 server {ntp}
 authenticate
!
commit
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco IOS-XR — MISCONFIGURED — Sample {index}
hostname {hn}
telnet ipv4 server max-servers 5
username admin
 group root-lr
 secret 5 admin
!
snmp-server community public
snmp-server community private
!
interface GigabitEthernet0/0/0/0
 ipv4 address {self.rand_ip()} 255.255.255.0
 no shutdown
!
commit
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco IOS-XR — EDGE CASE — Sample {index}
hostname {hn}
! Failed or uncommitted block
router isis 1
 is-type level-2-only
 ! missing net entity
!
"""


# =============================================================================
# 5. Juniper Junos
# =============================================================================
class JuniperJunosGenerator(ConfigGenerator):
    vendor = "Juniper Networks"
    platform = "Junos"
    model = "MX480"
    device_class = "router"
    network_role = "edge"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'STRICT_RPF']
    product = "MX Series"
    os_name = "Junos OS"
    os_version = "22.x"
    device_type = "router"
    category = "router"
    config_format = "junos_hierarchy"
    vendor_dir_name = "juniper_junos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""/* GAACA Dataset — Juniper Junos — SECURE — Sample {index} */
system {{
    host-name {hn};
    root-authentication {{
        encrypted-password "{pwd}";
    }}
    services {{
        ssh {{
            protocol-version v2;
            ciphers [ aes256-gcm@openssh.com aes256-ctr ];
            macs [ hmac-sha2-512 hmac-sha2-256 ];
            connection-limit 5;
            rate-limit 3;
        }}
    }}
    login {{
        user netops {{
            uid 2001;
            class super-user;
            authentication {{
                encrypted-password "{pwd}";
            }}
        }}
    }}
    syslog {{
        user * {{
            any emergency;
        }}
        host {syslog} {{
            any notice;
            authorization info;
        }}
        file messages {{
            any notice;
            authorization info;
        }}
    }}
    ntp {{
        server {ntp};
    }}
}}
interfaces {{
    ge-0/0/0 {{
        unit 0 {{
            description "WAN Uplink";
            family inet {{
                rpf-check {{
                    mode strict;
                }}
                address {self.rand_ip()}/30;
            }}
        }}
    }}
    fxp0 {{
        unit 0 {{
            family inet {{
                address {self.rand_ip()}/24;
            }}
        }}
    }}
}}
routing-options {{
    autonomous-system {self.rand_as_number()};
}}
protocols {{
    bgp {{
        group EXTERNAL-PEERS {{
            type external;
            neighbor {self.rand_ip()} {{
                peer-as {self.rand_as_number()};
                authentication-key "{pwd}";
            }}
        }}
    }}
    lldp {{
        disable;
    }}
}}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""/* GAACA Dataset — Juniper Junos — MISCONFIGURED — Sample {index} */
system {{
    host-name {hn};
    root-authentication {{
        plain-text-password-value "root123";
    }}
    services {{
        telnet;
        web-management {{
            http;
        }}
    }}
}}
snmp {{
    community public {{
        authorization read-write;
    }}
}}
interfaces {{
    ge-0/0/0 {{
        unit 0 {{
            family inet {{
                address {self.rand_ip()}/24;
            }}
        }}
    }}
}}
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""/* GAACA Dataset — Juniper Junos — EDGE CASE — Sample {index} */
system {{
    host-name {hn};
}}
routing-instances {{
    TEST-VRF {{
        instance-type virtual-router;
        /* Empty routing instance with no interfaces or routes */
    }}
}}
"""


# =============================================================================
# 6. Arista EOS
# =============================================================================
class AristaEOSGenerator(ConfigGenerator):
    vendor = "Arista Networks"
    platform = "EOS"
    model = "7280R"
    device_class = "switch"
    network_role = "datacenter_leaf"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'VRF', 'VLAN']
    product = "7280R / 7500R Router"
    os_name = "EOS"
    os_version = "4.30"
    device_type = "router"
    category = "router"
    config_format = "arista_eos_cli"
    vendor_dir_name = "arista_eos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Arista EOS — SECURE — Sample {index}
!
transceiver qsfp default-mode 4x10G
!
hostname {hn}
ip domain-name corp.internal
!
service password-encryption
!
management ssh
   protocol-version 2
   cipher aes256-gcm
   idle-timeout 10
   no shutdown
!
no management api http-commands
management api http-commands
   no shutdown
   protocol https
   protocol http shutdown
!
username admin privilege 15 role network-admin secret sha512 {pwd}
!
vrf instance MGMT
!
interface Management1
   vrf MGMT
   ip address {self.rand_ip()}/24
!
interface Ethernet1
   description WAN-PEERING
   no switchport
   ip address {self.rand_ip()}/30
!
router bgp {self.rand_as_number()}
   router-id {self.rand_ip()}
   neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
   neighbor {self.rand_ip()} password 7 {pwd}
!
logging host {syslog} vrf MGMT
ntp server vrf MGMT {ntp} prefer
!
banner login
Authorized Access Only! All activity logged.
EOF
!
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Arista EOS — MISCONFIGURED — Sample {index}
hostname {hn}
!
management telnet
   no shutdown
!
management api http-commands
   no shutdown
   protocol http
!
username admin privilege 15 secret 0 admin
snmp-server community public ro
snmp-server community private rw
!
interface Ethernet1
   no switchport
   ip address {self.rand_ip()}/24
!
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Arista EOS — EDGE CASE — Sample {index}
hostname {hn}
!
router bgp 65100
   ! missing router-id and address-family activation
   neighbor 192.0.2.1 remote-as 65200
!
"""


# =============================================================================
# 7. Huawei VRP
# =============================================================================
class HuaweiVRPGenerator(ConfigGenerator):
    vendor = "Huawei"
    platform = "VRP"
    model = "NE40E"
    device_class = "router"
    network_role = "core"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'URPF']
    product = "NetEngine / AR Router"
    os_name = "VRP"
    os_version = "V800R021"
    device_type = "router"
    category = "router"
    config_format = "huawei_vrp_cli"
    vendor_dir_name = "huawei_vrp"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Huawei VRP — SECURE — Sample {index}
sysname {hn}
#
undo info-center enable
info-center enable
info-center loghost {syslog}
#
undo telnet server enable
stelnet server enable
ssh server cipher aes256_gcm
ssh server key-exchange dh_group14_sha256
ssh user admin authentication-type password
ssh user admin service-type stelnet
#
aaa
 local-user admin password irreversible-cipher {pwd}
 local-user admin service-type stelnet
 local-user admin level 15
#
interface GigabitEthernet0/0/0
 description WAN-UPLINK
 ip address {self.rand_ip()} 255.255.255.252
 urpf strict
#
interface GigabitEthernet0/0/1
 ip address {self.rand_ip()} 255.255.255.0
#
bgp {self.rand_as_number()}
 router-id {self.rand_ip()}
 peer {self.rand_ip()} as-number {self.rand_as_number()}
 peer {self.rand_ip()} password cipher {pwd}
#
snmp-agent
snmp-agent sys-info version v3
snmp-agent group v3 SECGROUP privacy
snmp-agent usm-user v3 secuser group SECGROUP
#
ntp-service authentication enable
ntp-service unicast-server {ntp}
#
user-interface vty 0 4
 authentication-mode aaa
 user navigation level 15
 idle-timeout 5 0
 protocol inbound ssh
#
return
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Huawei VRP — MISCONFIGURED — Sample {index}
sysname {hn}
#
telnet server enable
#
aaa
 local-user admin password simple admin123
 local-user admin service-type telnet
 local-user admin level 3
#
snmp-agent community read public
snmp-agent community write private
#
interface GigabitEthernet0/0/0
 ip address {self.rand_ip()} 255.255.255.0
#
user-interface vty 0 4
 authentication-mode none
 idle-timeout 0 0
 protocol inbound all
#
return
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Huawei VRP — EDGE CASE — Sample {index}
sysname {hn}
#
ospf 1
 ! area defined with no interfaces
 area 0.0.0.0
#
return
"""


# =============================================================================
# 8. Aruba AOS-S
# =============================================================================
class ArubaAOSSGenerator(ConfigGenerator):
    vendor = "Aruba / HPE"
    platform = "AOS-S"
    model = "2930F"
    device_class = "switch"
    network_role = "distribution"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['OSPF']
    capabilities = ['OSPF', 'VLAN']
    product = "2930F / 3810M Routing Switch"
    os_name = "AOS-S"
    os_version = "16.10"
    device_type = "router"
    category = "router"
    config_format = "aruba_aoss_cli"
    vendor_dir_name = "aruba_aoss"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""; GAACA Dataset — Aruba AOS-S — SECURE — Sample {index}
hostname "{hn}"
ip routing
no telnet-server
no web-management
web-management ssl
crypto host-cert generate self-signed
ip ssh
ip ssh filetransfer
password manager user-name "admin" sha1 "{pwd}"
snmp-server community "public" disable
snmpv3 enable
snmpv3 group initial user "secadmin" sec-model ver3
snmpv3 user "secadmin" auth sha "{pwd}" priv aes "{pwd}"
logging {syslog}
sntp server priority 1 {ntp}
sntp mode unicast
sntp enable
vlan 1
   name "DEFAULT_VLAN"
   untagged 1-24
   ip address {self.rand_ip()} 255.255.255.0
   exit
router ospf
   enable
   area 0.0.0.0
   exit
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""; GAACA Dataset — Aruba AOS-S — MISCONFIGURED — Sample {index}
hostname "{hn}"
ip routing
telnet-server
web-management plaintext
password manager plaintext "admin"
snmp-server community "public" operator unrestricted
snmp-server community "private" manager unrestricted
vlan 1
   ip address {self.rand_ip()} 255.255.255.0
   exit
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""; GAACA Dataset — Aruba AOS-S — EDGE CASE — Sample {index}
hostname "{hn}"
router vrrp
   ! VRRP enabled without virtual router instance
exit
"""


# =============================================================================
# 9. Aruba AOS-CX
# =============================================================================
class ArubaAOSCXGenerator(ConfigGenerator):
    vendor = "Aruba / HPE"
    platform = "AOS-CX"
    model = "8325"
    device_class = "switch"
    network_role = "core"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'VRF', 'VLAN']
    product = "CX 8325 / 8400 Core Router"
    os_name = "AOS-CX"
    os_version = "10.12"
    device_type = "router"
    category = "router"
    config_format = "aruba_aoscx_cli"
    vendor_dir_name = "aruba_aoscx"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Aruba AOS-CX — SECURE — Sample {index}
hostname {hn}
ssh server vrf mgmt
no telnet-server
https-server vrf mgmt
user admin group administrators password ciphertext {pwd}
vrf instance mgmt
interface mgmt
    no shutdown
    ip static {self.rand_ip()}/24
    default-gateway {self.rand_ip()}
interface 1/1/1
    no shutdown
    routing
    ip address {self.rand_ip()}/30
router bgp {self.rand_as_number()}
    router-id {self.rand_ip()}
    neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
    neighbor {self.rand_ip()} password ciphertext {pwd}
logging {syslog} severity info vrf mgmt
ntp server {ntp} vrf mgmt
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Aruba AOS-CX — MISCONFIGURED — Sample {index}
hostname {hn}
telnet-server
no ssh server
user admin group administrators password plaintext admin
snmp-server community public
snmp-server community private rw
interface 1/1/1
    routing
    ip address {self.rand_ip()}/24
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Aruba AOS-CX — EDGE CASE — Sample {index}
hostname {hn}
router ospf 1
    ! empty ospf area
    area 0.0.0.0
"""


# =============================================================================
# 10. Extreme EXOS
# =============================================================================
class ExtremeEXOSGenerator(ConfigGenerator):
    vendor = "Extreme Networks"
    platform = "EXOS"
    model = "Summit X460"
    device_class = "switch"
    network_role = "aggregation"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['OSPF']
    capabilities = ['OSPF', 'VLAN']
    product = "Summit / SLX Router"
    os_name = "EXOS"
    os_version = "32.x"
    device_type = "router"
    category = "router"
    config_format = "extreme_exos_cli"
    vendor_dir_name = "extreme_exos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Extreme EXOS — SECURE — Sample {index}
configure snmp sysName "{hn}"
disable telnet
enable ssh2
configure ssh2 key 4096
disable web
configure account admin encrypted "{pwd}"
configure syslog add {syslog}:514 vr VR-Mgmt local0 notice
configure sntp-client add server {ntp} vr VR-Mgmt
enable sntp-client
configure vlan default delete ports all
create vlan "WAN-VLAN"
configure vlan "WAN-VLAN" tag {self.rand_vlan()}
configure vlan "WAN-VLAN" add ports 1:1 untagged
configure vlan "WAN-VLAN" ipaddress {self.rand_ip()}/30
enable ipforwarding vlan "WAN-VLAN"
configure rip disable
configure ospf add vlan "WAN-VLAN" area 0.0.0.0
enable ospf
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Extreme EXOS — MISCONFIGURED — Sample {index}
configure snmp sysName "{hn}"
enable telnet
disable ssh2
enable web
configure account admin password "admin"
configure snmp add community readonly "public"
configure snmp add community readwrite "private"
configure vlan default ipaddress {self.rand_ip()}/24
enable ipforwarding
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Extreme EXOS — EDGE CASE — Sample {index}
configure snmp sysName "{hn}"
create vlan "ORPHAN"
! VLAN created without ports or IP address
"""


# =============================================================================
# 11. Nokia SR OS
# =============================================================================
class NokiaSROSGenerator(ConfigGenerator):
    vendor = "Nokia"
    platform = "SR OS"
    model = "7750 SR"
    device_class = "router"
    network_role = "core"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'ROUTER_BASE']
    product = "7750 Service Router"
    os_name = "SR OS"
    os_version = "23.x"
    device_type = "router"
    category = "router"
    config_format = "nokia_sros_cli"
    vendor_dir_name = "nokia_sros"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Nokia SR OS — SECURE — Sample {index}
configure system name "{hn}"
configure system security telnet-server shutdown
configure system security ssh server-shutdown no
configure system security ssh ciphers-in aes256-gcm aes128-gcm
configure system security password min-length 14
configure system security user "admin" password "{pwd}"
configure system security user "admin" access console netconf
configure log syslog {syslog} facility local6
configure system ntp server {ntp} prefer
configure router Base
    interface "system"
        address {self.rand_ip()}/32
        no shutdown
    exit
    interface "to-core"
        port 1/1/1
        address {self.rand_ip()}/30
        no shutdown
    exit
    autonomous-system {self.rand_as_number()}
    bgp
        group "CORE-IBGP"
            peer-as {self.rand_as_number()}
            authentication-key "{pwd}"
            neighbor {self.rand_ip()}
            exit
        exit
        no shutdown
    exit
exit
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Nokia SR OS — MISCONFIGURED — Sample {index}
configure system name "{hn}"
configure system security telnet-server no shutdown
configure system security ssh server-shutdown
configure system security snmp community "public" r
configure system security snmp community "private" rw
configure system security user "admin" password "admin"
configure router Base
    interface "system"
        address {self.rand_ip()}/32
    exit
exit
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Nokia SR OS — EDGE CASE — Sample {index}
configure system name "{hn}"
configure router Base
    bgp
        ! empty BGP instance without groups or peers
    exit
exit
"""


# =============================================================================
# 12. Dell OS10
# =============================================================================
class DellOS10Generator(ConfigGenerator):
    vendor = "Dell Technologies"
    platform = "OS10"
    model = "PowerSwitch S5248F"
    device_class = "switch"
    network_role = "datacenter_leaf"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'VLAN']
    product = "PowerSwitch Z-Series"
    os_name = "OS10 Enterprise"
    os_version = "10.5.x"
    device_type = "router"
    category = "router"
    config_format = "dell_os10_cli"
    vendor_dir_name = "dell_os10"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Dell OS10 — SECURE — Sample {index}
hostname {hn}
no ip telnet server enable
ip ssh server enable
ip ssh server cipher aes256-ctr,aes128-gcm
username admin password {pwd} role sysadmin
interface mgmt1/1/1
 no shutdown
 ip address {self.rand_ip()}/24
!
interface ethernet1/1/1
 no shutdown
 no switchport
 ip address {self.rand_ip()}/30
!
router bgp {self.rand_as_number()}
 router-id {self.rand_ip()}
 neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
 neighbor {self.rand_ip()} password {pwd}
!
logging server {syslog}
ntp server {ntp}
!
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Dell OS10 — MISCONFIGURED — Sample {index}
hostname {hn}
ip telnet server enable
no ip ssh server enable
username admin password admin role sysadmin
snmp-server community public ro
snmp-server community private rw
interface ethernet1/1/1
 no switchport
 ip address {self.rand_ip()}/24
!
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Dell OS10 — EDGE CASE — Sample {index}
hostname {hn}
interface ethernet1/1/1
 ! unconfigured routed interface
 no switchport
!
"""


# =============================================================================
# 13. MikroTik RouterOS
# =============================================================================
class MikroTikRouterOSGenerator(ConfigGenerator):
    vendor = "MikroTik"
    platform = "RouterOS"
    model = "CCR2004"
    device_class = "router"
    network_role = "edge"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'ROUTING']
    product = "Cloud Core Router (CCR)"
    os_name = "RouterOS"
    os_version = "v7.x"
    device_type = "router"
    category = "router"
    config_format = "mikrotik_rsc"
    vendor_dir_name = "mikrotik_routeros"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — MikroTik RouterOS — SECURE — Sample {index}
/system identity set name="{hn}"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=no certificate=none port=443
/ip service set ssh disabled=no port=22 strong-crypto=yes
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set winbox disabled=yes
/user set admin password="{pwd}" group=full
/ip address add address={self.rand_ip()}/30 interface=ether1 comment="WAN"
/ip address add address={self.rand_ip()}/24 interface=ether2 comment="LAN"
/routing bgp template add name=default as={self.rand_as_number()} router-id={self.rand_ip()}
/routing bgp connection add name=peer1 remote.address={self.rand_ip()} remote.as={self.rand_as_number()} template=default md5-key="{pwd}"
/system logging action add name=syslog-remote target=remote remote={syslog}
/system logging add topics=critical,error,warning,info action=syslog-remote
/system ntp client set enabled=yes
/system ntp client servers add address={ntp}
/snmp set enabled=no
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — MikroTik RouterOS — MISCONFIGURED — Sample {index}
/system identity set name="{hn}"
/ip service set telnet disabled=no port=23
/ip service set www disabled=no port=80
/ip service set api disabled=no port=8728
/ip service set winbox disabled=no
/user set admin password="" group=full
/snmp set enabled=yes
/snmp community set [ find default=yes ] name=public write-access=yes
/ip address add address={self.rand_ip()}/24 interface=ether1
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — MikroTik RouterOS — EDGE CASE — Sample {index}
/system identity set name="{hn}"
/ip firewall filter add chain=input action=passthrough
"""


# =============================================================================
# 14. Ubiquiti EdgeOS
# =============================================================================
class UbiquitiEdgeOSGenerator(ConfigGenerator):
    vendor = "Ubiquiti Networks"
    platform = "EdgeOS"
    model = "ER-Pro8"
    device_class = "router"
    network_role = "branch"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'FIREWALL']
    product = "EdgeRouter Pro"
    os_name = "EdgeOS"
    os_version = "v2.0.x"
    device_type = "router"
    category = "router"
    config_format = "edgeos_text"
    vendor_dir_name = "ubiquiti_edgeos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""/* GAACA Dataset — Ubiquiti EdgeOS — SECURE — Sample {index} */
system {{
    host-name {hn}
    login {{
        user admin {{
            authentication {{
                encrypted-password "{pwd}"
            }}
            level admin
        }}
    }}
    ntp {{
        server {ntp} {{
        }}
    }}
    services {{
        ssh {{
            ciphers aes256-gcm@openssh.com
            listen-address {self.rand_ip()}
            port 22
            protocol-version v2
        }}
        gui {{
            http-port 80
            https-port 443
            older-ciphers disable
        }}
    }}
    syslog {{
        host {syslog} {{
            facility all {{
                level notice
            }}
        }}
    }}
}}
interfaces {{
    ethernet eth0 {{
        address {self.rand_ip()}/30
        description "WAN Uplink"
    }}
    ethernet eth1 {{
        address {self.rand_ip()}/24
        description "Local LAN"
    }}
}}
protocols {{
    bgp {self.rand_as_number()} {{
        neighbor {self.rand_ip()} {{
            remote-as {self.rand_as_number()}
            password "{pwd}"
        }}
    }}
}}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""/* GAACA Dataset — Ubiquiti EdgeOS — MISCONFIGURED — Sample {index} */
system {{
    host-name {hn}
    login {{
        user ubnt {{
            plaintext-password "ubnt"
            level admin
        }}
    }}
    services {{
        telnet {{
            listen-address 0.0.0.0
            port 23
        }}
        gui {{
            http-port 80
        }}
        snmp {{
            community public {{
                authorization ro
            }}
        }}
    }}
}}
interfaces {{
    ethernet eth0 {{
        address {self.rand_ip()}/24
    }}
}}
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""/* GAACA Dataset — Ubiquiti EdgeOS — EDGE CASE — Sample {index} */
system {{
    host-name {hn}
}}
protocols {{
    static {{
        /* Blackhole route edge case */
        route 0.0.0.0/0 {{
            blackhole {{
            }}
        }}
    }}
}}
"""


# =============================================================================
# 15. Ruijie RGOS
# =============================================================================
class RuijieRGOSGenerator(ConfigGenerator):
    vendor = "Ruijie Networks"
    platform = "RGOS"
    model = "RSR7700"
    device_class = "router"
    network_role = "core"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'ROUTING']
    product = "RSR Series Core Router"
    os_name = "RGOS"
    os_version = "11.x"
    device_type = "router"
    category = "router"
    config_format = "ruijie_rgos_cli"
    vendor_dir_name = "ruijie_rgos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Ruijie RGOS — SECURE — Sample {index}
hostname {hn}
service password-encryption
no enable password
enable secret {pwd}
username admin privilege 15 secret {pwd}
!
no telnet-server enable
ssh-server enable
ssh-server authentication-retries 3
ssh-server timeout 60
!
interface GigabitEthernet 0/0
 description WAN-OUT
 ip address {self.rand_ip()} 255.255.255.252
 no ip proxy-arp
 no shutdown
!
interface GigabitEthernet 0/1
 ip address {self.rand_ip()} 255.255.255.0
 no shutdown
!
router bgp {self.rand_as_number()}
 neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
 neighbor {self.rand_ip()} password {pwd}
!
logging server {syslog}
ntp server {ntp}
!
line vty 0 4
 login local
 transport input ssh
 exec-timeout 10 0
!
end
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruijie RGOS — MISCONFIGURED — Sample {index}
hostname {hn}
telnet-server enable
no ssh-server enable
enable password ruijie
username admin privilege 15 password ruijie
snmp-server community public ro
snmp-server community private rw
interface GigabitEthernet 0/0
 ip address {self.rand_ip()} 255.255.255.0
!
line vty 0 4
 login
 password ruijie
 transport input telnet
!
end
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruijie RGOS — EDGE CASE — Sample {index}
hostname {hn}
router ospf 10
 ! Empty area with no network statements
 area 1 stub
!
end
"""


# =============================================================================
# 16. H3C Comware
# =============================================================================
class H3CComwareGenerator(ConfigGenerator):
    vendor = "H3C"
    platform = "Comware"
    model = "MSR 3600"
    device_class = "router"
    network_role = "wan"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'ROUTING']
    product = "MSR / SR Series Router"
    os_name = "Comware"
    os_version = "v7"
    device_type = "router"
    category = "router"
    config_format = "h3c_comware_cli"
    vendor_dir_name = "h3c_comware"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — H3C Comware — SECURE — Sample {index}
sysname {hn}
#
undo telnet server enable
ssh server enable
ssh user admin service-type stelnet authentication-type password
#
local-user admin class manage
 password cipher {pwd}
 service-type stelnet
 authorization-attribute user-role network-admin
#
interface GigabitEthernet0/0
 description WAN-Uplink
 ip address {self.rand_ip()} 255.255.255.252
#
interface GigabitEthernet0/1
 ip address {self.rand_ip()} 255.255.255.0
#
bgp {self.rand_as_number()}
 router-id {self.rand_ip()}
 peer {self.rand_ip()} as-number {self.rand_as_number()}
 peer {self.rand_ip()} password cipher {pwd}
#
info-center loghost {syslog}
ntp-service unicast-server {ntp}
#
line vty 0 4
 authentication-mode scheme
 user-role network-admin
 idle-timeout 10 0
 protocol inbound ssh
#
return
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — H3C Comware — MISCONFIGURED — Sample {index}
sysname {hn}
#
telnet server enable
undo ssh server enable
#
local-user admin class manage
 password simple admin
 service-type telnet
 authorization-attribute user-role network-admin
#
snmp-agent community read public
snmp-agent community write private
#
line vty 0 4
 authentication-mode none
 user-role network-admin
#
return
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — H3C Comware — EDGE CASE — Sample {index}
sysname {hn}
#
interface Route-Aggregation1
 ! Empty aggregation group
#
return
"""


# =============================================================================
# 17. Allied Telesis AlliedWare Plus
# =============================================================================
class AlliedTelesisAWGenerator(ConfigGenerator):
    vendor = "Allied Telesis"
    platform = "AlliedWare Plus"
    model = "AR4050S"
    device_class = "router"
    network_role = "edge"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'FIREWALL']
    product = "AR4050S / AR3050S"
    os_name = "AlliedWare Plus"
    os_version = "5.5.x"
    device_type = "router"
    category = "router"
    config_format = "allied_telesis_cli"
    vendor_dir_name = "allied_telesis_aw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Allied Telesis — SECURE — Sample {index}
service password-encryption
hostname {hn}
!
no service http
service https
service ssh
no service telnet
!
username admin privilege 15 password 8 {pwd}
!
interface eth1
 description WAN-INTERNET
 ip address {self.rand_ip()}/30
 no shutdown
!
interface eth2
 description INTERNAL-LAN
 ip address {self.rand_ip()}/24
 no shutdown
!
router bgp {self.rand_as_number()}
 neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
 neighbor {self.rand_ip()} password {pwd}
!
log host {syslog}
ntp server {ntp}
!
line vty 0 4
 login local
 transport input ssh
 idle-timeout 10
!
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Allied Telesis — MISCONFIGURED — Sample {index}
hostname {hn}
service telnet
no service ssh
service http
no service https
username admin privilege 15 password 0 admin
snmp-server community public ro
snmp-server community private rw
interface eth1
 ip address {self.rand_ip()}/24
!
line vty 0 4
 login none
!
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Allied Telesis — EDGE CASE — Sample {index}
hostname {hn}
zone private
 network lan
! zone created without interface mapping
"""


# =============================================================================
# 18. SONiC Network OS
# =============================================================================
class SONiCConfigDBGenerator(ConfigGenerator):
    vendor = "Open Source / Linux Foundation"
    platform = "SONiC"
    model = "AS7726"
    device_class = "switch"
    network_role = "datacenter_leaf"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'VLAN']
    product = "SONiC Enterprise Router"
    os_name = "SONiC"
    os_version = "202311"
    device_type = "router"
    category = "router"
    config_format = "sonic_config_db_json"
    vendor_dir_name = "sonic_configdb"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        wan_ip = self.rand_ip()
        cfg = {
            "DEVICE_METADATA": {
                "localhost": {
                    "hostname": hn,
                    "hwsku": "Dell-EMC-Z9332f-O32",
                    "type": "ToRRouter",
                    "mac": "52:54:00:12:34:56",
                    "docker_routing_config_mode": "unified"
                }
            },
            "MGMT_INTERFACE": {
                f"eth0|{self.rand_ip()}/24": {
                    "gwaddr": self.rand_ip()
                }
            },
            "INTERFACE": {
                f"Ethernet0|{wan_ip}/30": {}
            },
            "BGP_NEIGHBOR": {
                f"{self.rand_ip()}": {
                    "asn": str(self.rand_as_number()),
                    "name": "CORE-ROUTER-01",
                    "holdtime": "180",
                    "keepalive": "60"
                }
            },
            "NTP_SERVER": {
                ntp: {}
            },
            "SYSLOG_SERVER": {
                syslog: {
                    "port": "514"
                }
            },
            "AAA": {
                "authentication": {
                    "login": "local",
                    "failthrough": "True"
                }
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "DEVICE_METADATA": {
                "localhost": {
                    "hostname": hn,
                    "hwsku": "Generic-Switch",
                    "type": "LeafRouter"
                }
            },
            "INTERFACE": {
                f"Ethernet0|{self.rand_ip()}/24": {}
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
            "ACL_TABLE": {
                "EMPTY_FILTER": {
                    "type": "L3",
                    "ports": []
                }
            }
        }
        return json.dumps(cfg, indent=4)


# =============================================================================
# 19. Brocade / Ruckus FastIron
# =============================================================================
class BrocadeFastIronGenerator(ConfigGenerator):
    vendor = "Brocade / Ruckus"
    platform = "FastIron"
    model = "ICX 7450"
    device_class = "switch"
    network_role = "distribution"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'VLAN']
    product = "NetIron / ICX Routing"
    os_name = "FastIron"
    os_version = "08.0.95"
    device_type = "router"
    category = "router"
    config_format = "brocade_cli"
    vendor_dir_name = "brocade_fastiron"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Brocade FastIron — SECURE — Sample {index}
ver 08.0.95
hostname {hn}
enable super-user-password 8 {pwd}
no telnet server
crypto key zeroize rsa
crypto key generate rsa modulus 2048
ip ssh server
ip ssh idle-time 10
username admin privilege 0 password 8 {pwd}
interface ethernet 1/1/1
 port-name WAN-LINK
 ip address {self.rand_ip()} 255.255.255.252
!
interface ethernet 1/1/2
 ip address {self.rand_ip()} 255.255.255.0
!
router bgp
 local-as {self.rand_as_number()}
 neighbor {self.rand_ip()} remote-as {self.rand_as_number()}
 neighbor {self.rand_ip()} password 8 {pwd}
!
logging host {syslog}
sntp server {ntp}
!
end
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Brocade FastIron — MISCONFIGURED — Sample {index}
ver 08.0.80
hostname {hn}
enable super-user-password 0 brocade
telnet server
no ip ssh server
snmp-server community public ro
snmp-server community private rw
interface ethernet 1/1/1
 ip address {self.rand_ip()} 255.255.255.0
!
end
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Brocade FastIron — EDGE CASE — Sample {index}
hostname {hn}
router rip
 ! empty RIP config
end
"""


# =============================================================================
# 20. VyOS
# =============================================================================
class VyOSGenerator(ConfigGenerator):
    vendor = "VyOS Project"
    platform = "VyOS"
    model = "VyOS 1.4"
    device_class = "router"
    network_role = "edge"
    routing_capability = True
    l3_capable = True
    routing_protocols = ['BGP']
    capabilities = ['BGP', 'FIREWALL']
    product = "VyOS Universal Router"
    os_name = "VyOS"
    os_version = "1.4.x"
    device_type = "router"
    category = "router"
    config_format = "vyos_cli"
    vendor_dir_name = "vyos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""// GAACA Dataset — VyOS — SECURE — Sample {index}
set system host-name '{hn}'
set system login user admin authentication encrypted-password '{pwd}'
set system login user admin level 'admin'
set service ssh port '22'
set service ssh ciphers 'aes256-gcm@openssh.com'
set service ssh disable-password-authentication
set system syslog host {syslog} facility all level 'notice'
set system ntp server {ntp}
set interfaces ethernet eth0 address '{self.rand_ip()}/30'
set interfaces ethernet eth0 description 'WAN-Uplink'
set interfaces ethernet eth1 address '{self.rand_ip()}/24'
set protocols bgp system-as '{self.rand_as_number()}'
set protocols bgp neighbor {self.rand_ip()} remote-as '{self.rand_as_number()}'
set protocols bgp neighbor {self.rand_ip()} password '{pwd}'
set firewall name WAN-IN default-action 'drop'
set firewall name WAN-IN rule 10 action 'accept'
set firewall name WAN-IN rule 10 state established 'enable'
set firewall name WAN-IN rule 10 state related 'enable'
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""// GAACA Dataset — VyOS — MISCONFIGURED — Sample {index}
set system host-name '{hn}'
set system login user vyos authentication plaintext-password 'vyos'
set service telnet
set service snmp community public authorization 'ro'
set service snmp community private authorization 'rw'
set interfaces ethernet eth0 address '{self.rand_ip()}/24'
set firewall name WAN-IN default-action 'accept'
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""// GAACA Dataset — VyOS — EDGE CASE — Sample {index}
set system host-name '{hn}'
set protocols static route 0.0.0.0/0 blackhole distance '254'
"""


# =============================================================================
# Registry of all router generators
# =============================================================================
ROUTER_GENERATORS = [
    CiscoIOSGenerator,
    CiscoIOSXEGenerator,
    CiscoNXOSGenerator,
    CiscoIOSXRGenerator,
    JuniperJunosGenerator,
    AristaEOSGenerator,
    HuaweiVRPGenerator,
    ArubaAOSSGenerator,
    ArubaAOSCXGenerator,
    ExtremeEXOSGenerator,
    NokiaSROSGenerator,
    DellOS10Generator,
    MikroTikRouterOSGenerator,
    UbiquitiEdgeOSGenerator,
    RuijieRGOSGenerator,
    H3CComwareGenerator,
    AlliedTelesisAWGenerator,
    SONiCConfigDBGenerator,
    BrocadeFastIronGenerator,
    VyOSGenerator,
]
