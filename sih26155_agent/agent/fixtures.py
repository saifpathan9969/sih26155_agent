"""
Six synthetic device configs, deliberately designed so a mission run
demonstrates every interesting path at once:
  - dev01 (Cisco): mostly hardened, should mostly PASS
  - dev02 (Cisco): Telnet left on, should FAIL that check
  - dev03 (Juniper): hardened EXCEPT one unmapped lockout line
  - dev04 (Juniper): same unmapped lockout pattern, slightly different wording
  - dev05 (Juniper): same unmapped lockout pattern again, different number
  - dev06 (FortiOS): vendor has no parser yet — everything degrades to
    "needs human review", demonstrating graceful handling of a genuinely
    unsupported vendor rather than a wrong guess
"""

DEVICE_CONFIGS = {
    "dev01_cisco.conf": """
Building configuration...
!
service password-encryption
security passwords min-length 14
login block-for 900 attempts 5 within 600
ip ssh version 2
line vty 0 4
 exec-timeout 10 0
 transport input ssh
 access-class 10 in
no ip http server
ip http secure-server
ip http tls-version TLSv1.2
snmp-server community Xk93Lp2q RO
logging host 10.0.0.5
logging buffered 65536
archive
 log config
ip ssh server algorithm encryption aes256-ctr
""",

    "dev02_cisco.conf": """
Building configuration...
!
service password-encryption
security passwords min-length 8
ip ssh version 2
line vty 0 4
 exec-timeout 10 0
 transport input telnet
no ip http server
snmp-server community public RO
logging host 10.0.0.5
logging buffered 8192
""",

    "dev03_juniper.conf": """
set system login password format sha256
set system login password minimum-length 14
set system services ssh protocol-version v2
set system login idle-timeout 10
delete system services telnet
delete system services web-management http
set system services web-management https
set system services web-management https tls-min-version tls1.2
set snmp v3
set firewall filter MGMT-ACCESS term allow-mgmt from source-address 10.0.0.0/24
set security pki ca-profile CA revocation-check crl
set system services ssh ciphers aes256-ctr
set system syslog host 10.0.0.5 any notice
set system syslog file change-log change-log any
set system login retry-options tries-before-disconnect 5 lockout-period 15
""",

    "dev04_juniper.conf": """
set system login password format sha256
set system login password minimum-length 14
set system services ssh protocol-version v2
delete system services telnet
delete system services web-management http
set system services web-management https
set snmp v3
set system syslog host 10.0.0.6 any notice
set system login retry-options tries-before-disconnect 5
""",

    "dev05_juniper.conf": """
set system login password format sha256
set system services ssh protocol-version v2
delete system services telnet
delete system services web-management http
set snmp v3
set system syslog host 10.0.0.7 any notice
set system login retry-options tries-before-disconnect 3 lockout-period 20
""",

    "dev06_fortinet.conf": """
config system global
    set admin-sport 443
    set admin-lockout-threshold 3
    set admin-lockout-duration 900
end
config firewall policy
    edit 1
        set srcintf internal
        set dstintf wan1
        set action accept
    next
end
""",

    "arista_eos_test.conf": """! Synthetic Arista EOS lab fixture for parser/understanding tests
! Not an official vendor hardening template.

hostname EOS-LAB-01
!
username admin privilege 15 secret 0 LabAdminPassword
enable secret 0 LabEnablePassword
!
management api http-commands
   no shutdown
!
no ip http server
!
interface Ethernet1
   description WAN
   no switchport
   ip address 203.0.113.2/30
   no shutdown
!
interface Ethernet2
   description LAN
   switchport access vlan 10
   no shutdown
!
interface Vlan10
   ip address 192.168.10.1/24
   no shutdown
!
ip routing
!
ip access-list standard MGMT-ONLY
   10 permit 192.168.10.0/24
   20 deny any
!
router ospf 10
   router-id 192.168.10.1
   network 192.168.10.0/24 area 0
!
router bgp 65010
   router-id 192.168.10.1
   neighbor 203.0.113.1 remote-as 65000
!
logging host 192.168.10.50
logging buffered 10000
!
ntp server 192.168.10.50
!
management api http-commands
   no shutdown
!
""",

    "aruba_aoscx_test.conf": """! Synthetic Aruba AOS-CX lab fixture for parser/understanding tests
! Not an official vendor hardening template.

hostname AOSCX-LAB-01
!
user admin group administrators password plaintext LabAdminPassword
!
ssh server vrf default
ssh server vrf mgmt
no telnet server
!
ntp server 192.168.10.50
ntp enable
!
logging 192.168.10.50
!
vlan 10
   name USERS
!
interface 1/1/1
   description WAN
   no shutdown
   routing
   ip address 203.0.113.6/30
!
interface 1/1/2
   description LAN
   no shutdown
   vlan access 10
!
interface vlan 10
   ip address 192.168.20.1/24
!
ip route 0.0.0.0/0 203.0.113.5
!
aaa authentication login default local
aaa authorization commands default local
!
access-list ip MGMT
   10 permit any 192.168.20.0/24 any
   20 deny any any any
!
security-profile experimental-policy-mode strict
""",

    "huawei_vrp_test.cfg": """# Synthetic Huawei VRP lab fixture for parser/understanding tests
# Not an official vendor hardening template.

sysname HUAWEI-LAB-01
#
aaa
 local-user admin password irreversible-cipher LabAdminPassword
 local-user admin privilege level 15
 local-user admin service-type ssh
#
stelnet server enable
undo telnet server enable
#
ssh server authentication-type default password
ssh user admin
#
interface GigabitEthernet0/0/0
 description WAN
 ip address 203.0.113.14 255.255.255.252
 undo shutdown
#
interface GigabitEthernet0/0/1
 description LAN
 ip address 192.168.40.1 255.255.255.0
 undo shutdown
#
ip route-static 0.0.0.0 0.0.0.0 203.0.113.13
#
acl number 3000
 rule 5 permit ip source 192.168.40.0 0.0.0.255
 rule 10 deny ip
#
snmp-agent
snmp-agent community read cipher LabReadCommunity
#
info-center loghost 192.168.40.50
#
ntp-service enable
ntp-service unicast-server 192.168.40.50
#
acl number 3999
 rule 5 permit ip
#
""",

    "mikrotik_routeros_test.rsc": """# Synthetic MikroTik RouterOS lab fixture for parser/understanding tests
# Not an official vendor hardening template.

# Identity
/system identity set name=MT-LAB-01

# Users
/user set admin password="LabAdminPassword"
/user add name=netadmin group=full password="LabNetAdminPassword"

# Services
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set ssh disabled=no
/ip service set api disabled=yes
/ip service set winbox disabled=no address=192.168.30.0/24

# Interfaces
/ip address add address=203.0.113.10/30 interface=ether1 comment=WAN
/ip address add address=192.168.30.1/24 interface=bridge comment=LAN

# DNS
/ip dns set servers=1.1.1.1,8.8.8.8 allow-remote-requests=no

# NTP
/system ntp client set enabled=yes
/system ntp client servers add address=pool.ntp.org

# Firewall
/ip firewall filter add chain=input action=accept connection-state=established,related
/ip firewall filter add chain=input action=accept protocol=icmp
/ip firewall filter add chain=input action=accept src-address=192.168.30.0/24 protocol=tcp dst-port=22
/ip firewall filter add chain=input action=drop in-interface=ether1
/ip firewall filter add chain=forward action=accept connection-state=established,related
/ip firewall filter add chain=forward action=accept src-address=192.168.30.0/24 out-interface=ether1
/ip firewall filter add chain=forward action=accept

# NAT
/ip firewall nat add chain=srcnat out-interface=ether1 action=masquerade

# Broad rule for auditor testing
/ip firewall filter add chain=input action=accept protocol=tcp dst-port=1-65535
""",

    "paloalto_test.conf": """# Synthetic PAN-OS lab fixture for parser/understanding tests
# Not an official vendor hardening template.

set deviceconfig system hostname PA-LAB-01
set deviceconfig system type static
set deviceconfig system ip-address 192.0.2.10
set deviceconfig system netmask 255.255.255.0
set deviceconfig system default-gateway 192.0.2.1
set deviceconfig system dns-setting servers primary 1.1.1.1
set deviceconfig system dns-setting servers secondary 8.8.8.8

set deviceconfig system service disable-telnet yes
set deviceconfig system service disable-http yes
set deviceconfig system service disable-ssh no

set network interface ethernet ethernet1/1 layer3 ip 203.0.113.10/30
set network interface ethernet ethernet1/2 layer3 ip 192.168.10.1/24

set rulebase security rules LAN-TO-INTERNET from TRUST to UNTRUST source 192.168.10.0/24 destination any application any service application-default action allow
set rulebase security rules LAN-TO-INTERNET log-start yes
set rulebase security rules LAN-TO-INTERNET log-end yes

set rulebase security rules ADMIN-SSH from UNTRUST to TRUST source any destination 192.168.10.10 application ssh service service-ssh action allow
set rulebase security rules ADMIN-SSH log-end yes

set rulebase security rules TEMP-ANY-ANY from any to any source any destination any application any service any action allow
set rulebase security rules TEMP-ANY-ANY log-end no

set network virtual-router default routing-table ip static-route DEFAULT destination 0.0.0.0/0 nexthop ip-address 192.0.2.1
""",

    "vyos_test.conf": """# Synthetic VyOS lab fixture for parser/understanding tests
# Not an official vendor hardening template.

set system host-name vyos-lab-01
set system login user admin authentication plaintext-password 'LabAdminPassword'

set service ssh port '22'
set service ssh listen-address '192.168.50.1'
set service ssh disable-password-authentication 'false'

set interfaces ethernet eth0 description 'WAN'
set interfaces ethernet eth0 address '203.0.113.18/30'
set interfaces ethernet eth1 description 'LAN'
set interfaces ethernet eth1 address '192.168.50.1/24'

set protocols static route 0.0.0.0/0 next-hop '203.0.113.17'

set system name-server '1.1.1.1'
set system name-server '8.8.8.8'

set service ntp server '192.168.50.50'

set firewall ipv4 name LAN-TO-WAN default-action 'accept'
set firewall ipv4 name LAN-TO-WAN rule 10 action 'accept'
set firewall ipv4 name LAN-TO-WAN rule 10 source address '192.168.50.0/24'
set firewall ipv4 name LAN-TO-WAN rule 10 outbound-interface name 'eth0'

set firewall ipv4 name WAN-IN default-action 'drop'
set firewall ipv4 name WAN-IN rule 10 action 'accept'
set firewall ipv4 name WAN-IN rule 10 state established 'enable'
set firewall ipv4 name WAN-IN rule 20 action 'accept'
set firewall ipv4 name WAN-IN rule 20 protocol 'tcp'
set firewall ipv4 name WAN-IN rule 20 destination port '22'
set firewall ipv4 name WAN-IN rule 20 source address '0.0.0.0/0'

set service experimental-policy audit-mode 'legacy'
""",
}
