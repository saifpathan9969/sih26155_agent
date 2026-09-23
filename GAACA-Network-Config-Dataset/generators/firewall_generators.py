"""
GAACA Dataset — Firewall Configuration Generators
====================================================
21 vendor generators for firewall configurations.
Each produces secure, misconfigured, and edge_case variants.
"""

from __future__ import annotations
from generators.base import ConfigGenerator


# =============================================================================
# 1. Cisco ASA
# =============================================================================
class CiscoASAGenerator(ConfigGenerator):
    vendor = "Cisco"
    product = "ASA"
    os_name = "ASA OS"
    os_version = "9.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "cisco_asa_cli"
    vendor_dir_name = "cisco_asa"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        radius = self.rand_radius()
        pwd = self.rand_password()
        mgmt_ip = self.rand_ip()
        return f"""! GAACA Dataset — Cisco ASA — SECURE — Sample {index}
! Generated for SIH26155 compliance auditor training
!
hostname {hn}
domain-name example.lab
!
enable password {pwd} encrypted
passwd {pwd} encrypted
!
interface GigabitEthernet0/0
 nameif outside
 security-level 0
 ip address {self.rand_ip()} 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 nameif inside
 security-level 100
 ip address {self.rand_ip()} 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 nameif dmz
 security-level 50
 ip address {self.rand_ip()} 255.255.255.0
 no shutdown
!
interface Management0/0
 nameif management
 security-level 100
 ip address {mgmt_ip} 255.255.255.0
 management-only
 no shutdown
!
! --- SSH Hardening ---
ssh version 2
ssh key-exchange group dh-group14-sha256
ssh timeout 5
ssh {self.rand_ip()} 255.255.255.255 management
ssh {self.rand_ip()} 255.255.255.0 inside
no ssh outside
!
! --- Telnet Disabled ---
no telnet inside
no telnet outside
no telnet management
!
! --- HTTP/HTTPS Management ---
no http server enable
http server enable 8443
http {mgmt_ip} 255.255.255.0 management
ssl server-version tlsv1.2
ssl cipher tlsv1.2 custom "AES256-SHA256:DHE-RSA-AES256-SHA256"
!
! --- Authentication / AAA ---
aaa-server RADIUS-SVR protocol radius
aaa-server RADIUS-SVR (management) host {radius}
 key {self.rand_psk()}
 authentication-port 1812
 accounting-port 1813
 timeout 5
 retry-interval 3
!
aaa authentication ssh console RADIUS-SVR LOCAL
aaa authentication http console RADIUS-SVR LOCAL
aaa authentication enable console RADIUS-SVR LOCAL
aaa accounting command RADIUS-SVR
aaa accounting connection RADIUS-SVR
!
username admin password {pwd} encrypted privilege 15
username admin attributes
 service-type admin
!
! --- Password Policy ---
password-policy minimum-length 14
password-policy minimum-uppercase 1
password-policy minimum-lowercase 1
password-policy minimum-numeric 1
password-policy minimum-special 1
password-policy lifetime 90
!
! --- Login Attempt Lockout ---
aaa local authentication attempts max-fail 3
!
! --- SNMP v3 Only ---
no snmp-server enable
snmp-server group SNMPV3GRP v3 priv
snmp-server user snmpv3admin SNMPV3GRP v3 auth sha {pwd} priv aes 256 {pwd}
snmp-server host management {syslog} trap version 3 snmpv3admin
!
! --- Logging ---
logging enable
logging timestamp
logging buffer-size 1048576
logging buffered informational
logging trap informational
logging host management {syslog}
logging asdm informational
logging facility 20
!
! --- NTP ---
ntp authenticate
ntp authentication-key 1 md5 {self.rand_psk()}
ntp trusted-key 1
ntp server {ntp} key 1 prefer
!
! --- DNS ---
dns domain-lookup outside
dns server-group DefaultDNS
 name-server {self.rand_dns()}
!
! --- Access Control (Default Deny) ---
access-list OUTSIDE-IN extended deny ip any any log
access-group OUTSIDE-IN in interface outside
!
access-list INSIDE-OUT extended permit tcp {self.rand_ip()} 255.255.255.0 any eq 443
access-list INSIDE-OUT extended permit tcp {self.rand_ip()} 255.255.255.0 any eq 80
access-list INSIDE-OUT extended permit udp {self.rand_ip()} 255.255.255.0 any eq 53
access-list INSIDE-OUT extended deny ip any any log
access-group INSIDE-OUT in interface inside
!
! --- Banner ---
banner login WARNING: Authorized users only. All activity is monitored and logged.
!
! --- Console Timeout ---
console timeout 5
!
! --- Unused Services Disabled ---
no service dhcp
no service call-home
!
! --- Threat Detection ---
threat-detection basic-threat
threat-detection statistics access-list
threat-detection statistics tcp-intercept rate-interval 30 burst-rate 400 average-rate 200
!
end
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco ASA — MISCONFIGURED — Sample {index}
!
hostname {hn}
!
enable password cisco
passwd cisco
!
interface GigabitEthernet0/0
 nameif outside
 security-level 0
 ip address {self.rand_ip()} 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 nameif inside
 security-level 100
 ip address {self.rand_ip()} 255.255.255.0
 no shutdown
!
! --- INSECURE: Telnet enabled ---
telnet {self.rand_ip()} 255.255.255.0 inside
telnet timeout 30
!
! --- INSECURE: SSH v1 allowed ---
ssh version 1
ssh 0.0.0.0 0.0.0.0 outside
ssh timeout 60
!
! --- INSECURE: HTTP management enabled (no HTTPS) ---
http server enable
http 0.0.0.0 0.0.0.0 inside
http 0.0.0.0 0.0.0.0 outside
!
! --- INSECURE: No AAA, local only with weak password ---
username admin password admin privilege 15
!
! --- INSECURE: SNMP v2c with default community ---
snmp-server enable
snmp-server community public
snmp-server community private
snmp-server host inside {self.rand_ip()} community public version 2c
!
! --- INSECURE: No logging ---
no logging enable
!
! --- INSECURE: No NTP ---
no ntp server
!
! --- INSECURE: Any-Any permit ---
access-list OUTSIDE-IN extended permit ip any any
access-group OUTSIDE-IN in interface outside
!
access-list INSIDE-OUT extended permit ip any any
access-group INSIDE-OUT in interface inside
!
! --- No banner ---
!
! --- No console timeout ---
console timeout 0
!
end
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        scenarios = [
            # Partial config — only management section
            f"""! GAACA Dataset — Cisco ASA — EDGE CASE — Sample {index}
! Partial configuration — management plane only
hostname {hn}
ssh version 2
ssh timeout 5
ssh {self.rand_ip()} 255.255.255.0 management
enable password {self.rand_password()} encrypted
! Rest of configuration not present
""",
            # Deprecated syntax
            f"""! GAACA Dataset — Cisco ASA — EDGE CASE — Sample {index}
! Deprecated/legacy syntax mix
hostname {hn}
fixup protocol http 80
fixup protocol smtp 25
fixup protocol ftp 21
conduit permit tcp host {self.rand_ip()} eq 443 any
conduit permit tcp host {self.rand_ip()} eq 80 any
static (inside,outside) {self.rand_ip()} {self.rand_ip()} netmask 255.255.255.255
nat (inside) 1 0.0.0.0 0.0.0.0
global (outside) 1 interface
! Mixed with modern commands
access-list OUTSIDE-IN extended deny ip any any log
ssh version 2
end
""",
            # Conflicting rules
            f"""! GAACA Dataset — Cisco ASA — EDGE CASE — Sample {index}
! Conflicting access rules
hostname {hn}
!
access-list OUTSIDE-IN extended permit tcp any host {self.rand_ip()} eq 443
access-list OUTSIDE-IN extended deny tcp any host {self.rand_ip()} eq 443
access-list OUTSIDE-IN extended permit ip any any
access-list OUTSIDE-IN extended deny ip any any log
access-group OUTSIDE-IN in interface outside
!
! SSH enabled but also telnet
ssh version 2
ssh {self.rand_ip()} 255.255.255.0 management
telnet {self.rand_ip()} 255.255.255.0 inside
!
! SNMP v3 configured but v2 community also set
snmp-server group SNMPV3GRP v3 priv
snmp-server community public
!
end
""",
        ]
        return scenarios[(index - 1) % len(scenarios)]


# =============================================================================
# 2. Fortinet FortiGate
# =============================================================================
class FortinetFortiGateGenerator(ConfigGenerator):
    vendor = "Fortinet"
    product = "FortiGate"
    os_name = "FortiOS"
    os_version = "7.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "fortios_cli"
    vendor_dir_name = "fortinet_fortigate"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        radius = self.rand_radius()
        pwd = self.rand_password()
        return f"""# GAACA Dataset — FortiGate — SECURE — Sample {index}
config system global
    set hostname "{hn}"
    set timezone 04
    set admin-sport 8443
    set admin-ssh-port 22
    set admintimeout 10
    set admin-ssh-v1 disable
    set admin-telnet disable
    set admin-https-ssl-versions tlsv1-2 tlsv1-3
    set strong-crypto enable
    set admin-lockout-threshold 3
    set admin-lockout-duration 300
    set pre-login-banner enable
    set post-login-banner enable
end

config system interface
    edit "port1"
        set vdom "root"
        set mode static
        set ip {self.rand_ip()} 255.255.255.252
        set allowaccess ping
        set description "WAN-Uplink"
        set role wan
    next
    edit "port2"
        set vdom "root"
        set mode static
        set ip {self.rand_ip()} 255.255.255.0
        set allowaccess ping https ssh
        set description "LAN-Internal"
        set role lan
    next
    edit "port3"
        set vdom "root"
        set mode static
        set ip {self.rand_ip()} 255.255.255.0
        set allowaccess ping
        set description "DMZ"
        set role dmz
    next
    edit "mgmt"
        set vdom "root"
        set mode static
        set ip {self.rand_ip()} 255.255.255.0
        set allowaccess https ssh
        set description "Management"
        set dedicated-to management
    next
end

config system admin
    edit "admin"
        set accprofile "super_admin"
        set password {pwd}
        set force-password-change enable
        set two-factor fortitoken
        set trusthost1 {self.rand_ip()} 255.255.255.0
    next
end

config system password-policy
    set status enable
    set min-length 14
    set min-upper-case-letter 1
    set min-lower-case-letter 1
    set min-number 1
    set min-non-alphanumeric 1
    set expire-status enable
    set expire-day 90
    set reuse-password disable
end

config user radius
    edit "RADIUS-PRIMARY"
        set server "{radius}"
        set secret {self.rand_psk()}
        set radius-port 1812
        set acct-all-servers enable
    next
end

config system snmp sysinfo
    set status enable
    set description "{hn}"
    set contact-info "security-team@example.lab"
    set location "Datacenter-A"
end

config system snmp community
    edit 1
        set name "{self.rand_community()}"
        set status disable
    next
end

config system snmp user
    edit "snmpv3admin"
        set security-level auth-priv
        set auth-proto sha256
        set auth-pwd {pwd}
        set priv-proto aes256
        set priv-pwd {pwd}
        set notify-hosts {syslog}
    next
end

config log syslogd setting
    set status enable
    set server "{syslog}"
    set port 514
    set facility local7
    set source-ip {self.rand_ip()}
    set format default
    set enc-algorithm high
end

config log setting
    set fwpolicy-implicit-log enable
    set local-in-allow enable
    set local-in-deny-unicast enable
    set local-out enable
end

config system ntp
    set ntpsync enable
    set type custom
    set syncinterval 60
    config ntpserver
        edit 1
            set server "{ntp}"
            set ntpv3 enable
        next
    end
end

config firewall policy
    edit 1
        set name "LAN-to-WAN-Web"
        set srcintf "port2"
        set dstintf "port1"
        set srcaddr "all"
        set dstaddr "all"
        set action accept
        set schedule "always"
        set service "HTTPS" "DNS"
        set logtraffic all
        set utm-status enable
        set av-profile "default"
        set ips-sensor "default"
        set ssl-ssh-profile "deep-inspection"
    next
    edit 2
        set name "Default-Deny"
        set srcintf "any"
        set dstintf "any"
        set srcaddr "all"
        set dstaddr "all"
        set action deny
        set schedule "always"
        set service "ALL"
        set logtraffic all
    next
end

config system replacemsg admin "pre-login-disclaimer"
    set buffer "WARNING: Authorized access only. Activity is logged and monitored."
end
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — FortiGate — MISCONFIGURED — Sample {index}
config system global
    set hostname "{hn}"
    set admin-sport 443
    set admintimeout 0
    set admin-ssh-v1 enable
    set admin-telnet enable
    set admin-https-ssl-versions tlsv1-0 tlsv1-1 tlsv1-2
    set strong-crypto disable
    set admin-lockout-threshold 0
end

config system interface
    edit "port1"
        set vdom "root"
        set ip {self.rand_ip()} 255.255.255.252
        set allowaccess ping https ssh http telnet snmp
        set role wan
    next
    edit "port2"
        set vdom "root"
        set ip {self.rand_ip()} 255.255.255.0
        set allowaccess ping https ssh http telnet snmp fgfm
        set role lan
    next
end

config system admin
    edit "admin"
        set accprofile "super_admin"
        set password admin
    next
end

config system password-policy
    set status disable
end

config system snmp community
    edit 1
        set name "public"
        set status enable
        config hosts
            edit 1
                set ip 0.0.0.0 0.0.0.0
            next
        end
        set events cpu-high mem-low log-full
    next
    edit 2
        set name "private"
        set status enable
    next
end

config log syslogd setting
    set status disable
end

config log setting
    set fwpolicy-implicit-log disable
    set local-in-allow disable
    set local-in-deny-unicast disable
end

config system ntp
    set ntpsync disable
end

config firewall policy
    edit 1
        set name "Allow-All"
        set srcintf "any"
        set dstintf "any"
        set srcaddr "all"
        set dstaddr "all"
        set action accept
        set schedule "always"
        set service "ALL"
        set logtraffic disable
        set utm-status disable
    next
end
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        scenarios = [
            f"""# GAACA Dataset — FortiGate — EDGE CASE — Sample {index}
# Partial config — global settings only
config system global
    set hostname "{hn}"
    set timezone 04
end
# No interfaces, no policies, no logging configured
""",
            f"""# GAACA Dataset — FortiGate — EDGE CASE — Sample {index}
# Mixed security — some hardened, some not
config system global
    set hostname "{hn}"
    set admin-ssh-v1 disable
    set admin-telnet enable
    set strong-crypto enable
    set admin-lockout-threshold 0
end

config log syslogd setting
    set status enable
    set server "{self.rand_syslog()}"
end

config system snmp community
    edit 1
        set name "public"
        set status enable
    next
end

config firewall policy
    edit 1
        set name "Allow-All-Temp"
        set srcintf "any"
        set dstintf "any"
        set srcaddr "all"
        set dstaddr "all"
        set action accept
        set schedule "always"
        set service "ALL"
        set logtraffic all
    next
end
""",
        ]
        return scenarios[(index - 1) % len(scenarios)]


# =============================================================================
# 3. Palo Alto PAN-OS
# =============================================================================
class PaloAltoPANOSGenerator(ConfigGenerator):
    vendor = "Palo Alto Networks"
    product = "PAN-OS"
    os_name = "PAN-OS"
    os_version = "11.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "panos_set_cli"
    vendor_dir_name = "paloalto_panos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        radius = self.rand_radius()
        return f"""# GAACA Dataset — PAN-OS — SECURE — Sample {index}
set deviceconfig system hostname {hn}
set deviceconfig system domain example.lab
set deviceconfig system timezone US/Eastern
set deviceconfig system login-banner "WARNING: Authorized access only. All activity is monitored."
set deviceconfig system dns-setting servers primary {self.rand_dns()}
set deviceconfig system ntp-servers primary-ntp-server ntp-server-address {ntp}
set deviceconfig system ntp-servers primary-ntp-server authentication-type autokey

set deviceconfig setting management idle-timeout 10
set deviceconfig setting management admin-lockout enabled yes
set deviceconfig setting management admin-lockout lockout-time 30
set deviceconfig setting management admin-lockout failed-attempts 3

set deviceconfig system service disable-telnet yes
set deviceconfig system service disable-http yes
set deviceconfig system permitted-ip {self.rand_ip()}/32

set network interface ethernet ethernet1/1 layer3 ip {self.rand_ip()}/30
set network interface ethernet ethernet1/1 comment "WAN-Uplink"
set network interface ethernet ethernet1/2 layer3 ip {self.rand_ip()}/24
set network interface ethernet ethernet1/2 comment "LAN-Trusted"
set network interface ethernet ethernet1/3 layer3 ip {self.rand_ip()}/24
set network interface ethernet ethernet1/3 comment "DMZ"

set network zones untrust network layer3 ethernet1/1
set network zones trust network layer3 ethernet1/2
set network zones dmz network layer3 ethernet1/3

set shared log-settings syslog SYSLOG-PRIMARY server SRV1 server {syslog}
set shared log-settings syslog SYSLOG-PRIMARY server SRV1 transport UDP
set shared log-settings syslog SYSLOG-PRIMARY server SRV1 port 514
set shared log-settings syslog SYSLOG-PRIMARY server SRV1 facility LOG_LOCAL7

set shared log-settings profiles default match-list traffic-log send-syslog SYSLOG-PRIMARY
set shared log-settings profiles default match-list threat-log send-syslog SYSLOG-PRIMARY
set shared log-settings profiles default match-list config-log send-syslog SYSLOG-PRIMARY
set shared log-settings profiles default match-list system-log send-syslog SYSLOG-PRIMARY

set mgt-config users admin phash {self.rand_password()}
set mgt-config users admin permissions role-based superuser yes

set shared server-profile radius RADIUS-PRIMARY server SRV1 ip-address {radius}
set shared server-profile radius RADIUS-PRIMARY server SRV1 secret {self.rand_psk()}
set shared server-profile radius RADIUS-PRIMARY server SRV1 port 1812

set shared authentication-profile RADIUS-PROFILE method radius
set shared authentication-profile RADIUS-PROFILE server-profile RADIUS-PRIMARY
set shared authentication-profile RADIUS-PROFILE lockout failed-attempts 3
set shared authentication-profile RADIUS-PROFILE lockout lockout-time 30

set rulebase security rules ALLOW-LAN-WEB from trust to untrust application ssl web-browsing dns
set rulebase security rules ALLOW-LAN-WEB action allow
set rulebase security rules ALLOW-LAN-WEB log-end yes
set rulebase security rules ALLOW-LAN-WEB profile-setting group STRICT-SECURITY

set rulebase security rules DEFAULT-DENY from any to any application any
set rulebase security rules DEFAULT-DENY action deny
set rulebase security rules DEFAULT-DENY log-end yes

set deviceconfig system snmp-setting access-setting version v3
set deviceconfig system snmp-setting snmp-system contact "security-team@example.lab"
set deviceconfig system snmp-setting snmp-system location "DC-PRIMARY"

set shared ssl-tls-service-profile MGMT-TLS min-version tls1-2
set shared ssl-tls-service-profile MGMT-TLS max-version max
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — PAN-OS — MISCONFIGURED — Sample {index}
set deviceconfig system hostname {hn}
set deviceconfig system service disable-telnet no
set deviceconfig system service disable-http no
set deviceconfig setting management idle-timeout 0
set deviceconfig setting management admin-lockout enabled no

set network interface ethernet ethernet1/1 layer3 ip {self.rand_ip()}/30
set network interface ethernet ethernet1/2 layer3 ip {self.rand_ip()}/24

set mgt-config users admin phash admin123

set rulebase security rules ALLOW-ALL from any to any application any
set rulebase security rules ALLOW-ALL action allow
set rulebase security rules ALLOW-ALL log-end no

set shared ssl-tls-service-profile MGMT-TLS min-version tls1-0
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — PAN-OS — EDGE CASE — Sample {index}
# Panorama-pushed config fragment with device-group references
set device-group DG-BRANCH pre-rulebase security rules ALLOW-WEB from trust to untrust
set device-group DG-BRANCH pre-rulebase security rules ALLOW-WEB application ssl web-browsing
set device-group DG-BRANCH pre-rulebase security rules ALLOW-WEB action allow
set device-group DG-BRANCH post-rulebase security rules DENY-ALL from any to any
set device-group DG-BRANCH post-rulebase security rules DENY-ALL action deny
set template-stack TS-BRANCH templates BRANCH-BASE
set template-stack TS-BRANCH templates BRANCH-OVERLAY
# Missing base config — hostname, interfaces, zones not defined
"""


# =============================================================================
# 4. Check Point Gaia
# =============================================================================
class CheckPointGaiaGenerator(ConfigGenerator):
    vendor = "Check Point"
    product = "Security Gateway"
    os_name = "Gaia"
    os_version = "R81.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "checkpoint_clish"
    vendor_dir_name = "checkpoint_gaia"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Check Point Gaia — SECURE — Sample {index}
set hostname {hn}
set domainname example.lab

set interface eth0 ipv4-address {self.rand_ip()} mask-length 30
set interface eth0 state on
set interface eth0 comments "WAN-External"

set interface eth1 ipv4-address {self.rand_ip()} mask-length 24
set interface eth1 state on
set interface eth1 comments "LAN-Internal"

set interface eth2 ipv4-address {self.rand_ip()} mask-length 24
set interface eth2 state on
set interface eth2 comments "DMZ"

set static-route default nexthop gateway address {self.rand_ip()} on

set timezone America / New_York

set ntp active on
set ntp server primary {ntp} version 4
set ntp server secondary {self.rand_ntp()} version 4

set syslog log-remote-address {syslog}
set syslog log-remote-port 514
set syslog log-remote-protocol udp

set web ssl-port 4434
set web disable-http on

set inactivity-timeout 10
set user admin shell /etc/cli.sh
set expert-password-hash {self.rand_password()}

set core-dump enable off

set snmp agent on
set snmp agent-version v3-Only
set snmp trap-receiver {syslog} version v3 usm-user snmpv3admin

set aaa tacacs-servers priority 1 host {self.rand_tacacs()} timeout 5
set aaa tacacs-servers priority 1 secret {self.rand_psk()}

set message banner on
set message banner msg "WARNING: Authorized users only."

set ssh server version 2
set ssh server ciphers aes256-ctr
set ssh server mac hmac-sha2-256

set password-controls min-password-length 14
set password-controls complexity 4
set password-controls password-expiration 90
set password-controls password-history 12
set password-controls account-lockout true
set password-controls failed-attempts-allowed 3
set password-controls lockout-duration 300
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Check Point Gaia — MISCONFIGURED — Sample {index}
set hostname {hn}
set interface eth0 ipv4-address {self.rand_ip()} mask-length 30
set interface eth0 state on
set interface eth1 ipv4-address {self.rand_ip()} mask-length 24
set interface eth1 state on

set web ssl-port 443
set web disable-http off

set inactivity-timeout 0

set snmp agent on
set snmp agent-version any-version
set snmp community public read-only
set snmp community private read-write

set ssh server version any

set password-controls min-password-length 4
set password-controls complexity 0
set password-controls account-lockout false

set ntp active off
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Check Point Gaia — EDGE CASE — Sample {index}
# Minimal SecurePlatform-era config fragment
set hostname {self.rand_hostname()}
set interface eth0 ipv4-address {self.rand_ip()} mask-length 24
set interface eth0 state on
# No security settings, no routing, no logging
# cpconfig not run — implied defaults
"""


# =============================================================================
# 5. Juniper SRX
# =============================================================================
class JuniperSRXGenerator(ConfigGenerator):
    vendor = "Juniper"
    product = "SRX"
    os_name = "Junos"
    os_version = "23.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "junos_set"
    vendor_dir_name = "juniper_srx"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        radius = self.rand_radius()
        return f"""# GAACA Dataset — Juniper SRX — SECURE — Sample {index}
set system host-name {hn}
set system domain-name example.lab
set system time-zone America/New_York
set system login message "\\nWARNING: Authorized access only. Activity is logged.\\n"

set system services ssh protocol-version v2
set system services ssh ciphers aes256-ctr
set system services ssh macs hmac-sha2-256
set system services ssh rate-limit 5
set system services ssh root-login deny
delete system services telnet
delete system services web-management http

set system services web-management https system-generated-certificate
set system services web-management https port 4443
set system services web-management session idle-timeout 10

set system login user admin class super-user
set system login user admin authentication encrypted-password "{self.rand_password()}"
set system login retry-options tries-before-disconnect 3
set system login retry-options backoff-threshold 1
set system login retry-options backoff-factor 6
set system login retry-options lockout-period 5
set system login retry-options minimum-time 30

set system authentication-order radius password
set system radius-server {radius} secret "{self.rand_psk()}"
set system radius-server {radius} timeout 5
set system radius-server {radius} retry 3

set system syslog host {syslog} any info
set system syslog host {syslog} authorization any
set system syslog host {syslog} change-log any
set system syslog host {syslog} interactive-commands any
set system syslog file messages any info
set system syslog file messages authorization info
set system syslog file interactive-commands interactive-commands any
set system syslog time-override

set system ntp server {ntp}
set system ntp server {self.rand_ntp()}
set system ntp authentication-key 1 type md5 value "{self.rand_psk()}"
set system ntp trusted-key 1
set system ntp server {ntp} key 1

set system name-server {self.rand_dns()}

set interfaces ge-0/0/0 unit 0 family inet address {self.rand_ip()}/30
set interfaces ge-0/0/0 description "WAN-Uplink"
set interfaces ge-0/0/1 unit 0 family inet address {self.rand_ip()}/24
set interfaces ge-0/0/1 description "LAN-Internal"
set interfaces ge-0/0/2 unit 0 family inet address {self.rand_ip()}/24
set interfaces ge-0/0/2 description "DMZ"
set interfaces lo0 unit 0 family inet address {self.rand_ip()}/32

set security zones security-zone untrust interfaces ge-0/0/0 host-inbound-traffic system-services ping
set security zones security-zone trust interfaces ge-0/0/1 host-inbound-traffic system-services ping
set security zones security-zone trust interfaces ge-0/0/1 host-inbound-traffic system-services ssh
set security zones security-zone trust interfaces ge-0/0/1 host-inbound-traffic system-services https
set security zones security-zone dmz interfaces ge-0/0/2 host-inbound-traffic system-services ping

set security policies from-zone trust to-zone untrust policy allow-web match source-address any
set security policies from-zone trust to-zone untrust policy allow-web match destination-address any
set security policies from-zone trust to-zone untrust policy allow-web match application junos-https
set security policies from-zone trust to-zone untrust policy allow-web match application junos-dns-udp
set security policies from-zone trust to-zone untrust policy allow-web then permit
set security policies from-zone trust to-zone untrust policy allow-web then log session-close

set security policies default-policy deny-all
set security policies global policy default-deny match source-address any
set security policies global policy default-deny match destination-address any
set security policies global policy default-deny match application any
set security policies global policy default-deny then deny
set security policies global policy default-deny then log session-close

set snmp v3 usm local-engine user snmpv3admin authentication-sha authentication-key "{self.rand_password()}"
set snmp v3 usm local-engine user snmpv3admin privacy-aes128 privacy-key "{self.rand_password()}"
set snmp v3 target-address SYSLOG-TARGET address {syslog}
delete snmp community
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Juniper SRX — MISCONFIGURED — Sample {index}
set system host-name {hn}
set system services ssh protocol-version v1v2
set system services ssh root-login allow
set system services telnet
set system services web-management http
set system services web-management https
set system login user admin class super-user
set system login user admin authentication plain-text-password-value "admin"

set interfaces ge-0/0/0 unit 0 family inet address {self.rand_ip()}/30
set interfaces ge-0/0/1 unit 0 family inet address {self.rand_ip()}/24

set security policies from-zone trust to-zone untrust policy allow-all match source-address any
set security policies from-zone trust to-zone untrust policy allow-all match destination-address any
set security policies from-zone trust to-zone untrust policy allow-all match application any
set security policies from-zone trust to-zone untrust policy allow-all then permit

set security policies from-zone untrust to-zone trust policy allow-all match source-address any
set security policies from-zone untrust to-zone trust policy allow-all match destination-address any
set security policies from-zone untrust to-zone trust policy allow-all match application any
set security policies from-zone untrust to-zone trust policy allow-all then permit

set snmp community public authorization read-only

delete system syslog
delete system ntp
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Juniper SRX — EDGE CASE — Sample {index}
# ScreenOS-era commands mixed with Junos
set system host-name {self.rand_hostname()}
set interface ethernet0/0 ip {self.rand_ip()}/24
set interface ethernet0/0 zone trust
set policy from trust to untrust any any any permit log
set admin manager-ip {self.rand_ip()}/32
set admin ssh enable
set admin telnet disable
# These ScreenOS commands would fail on Junos
"""


# =============================================================================
# 6. Sophos XG
# =============================================================================
class SophosXGGenerator(ConfigGenerator):
    vendor = "Sophos"
    product = "Sophos Firewall"
    os_name = "SFOS"
    os_version = "20.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "sophos_cli"
    vendor_dir_name = "sophos_xg"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Sophos XG — SECURE — Sample {index}
console> system hostname {hn}
console> system admin timeout 10
console> system admin-password complexity enable
console> system admin-password min-length 14
console> system admin-password lockout-attempts 3
console> system admin-password lockout-duration 300

console> interface Port1 ipaddress {self.rand_ip()} netmask 255.255.255.252
console> interface Port1 zone WAN
console> interface Port1 gateway {self.rand_ip()}
console> interface Port2 ipaddress {self.rand_ip()} netmask 255.255.255.0
console> interface Port2 zone LAN
console> interface Port3 ipaddress {self.rand_ip()} netmask 255.255.255.0
console> interface Port3 zone DMZ

console> service ssh enable
console> service ssh port 22
console> service ssh v2-only enable
console> service telnet disable
console> service http-admin disable
console> service https-admin enable
console> service https-admin port 4444

console> log syslog add server {syslog} port 514 protocol UDP facility LOCAL7
console> log syslog severity informational

console> ntp enable
console> ntp server {ntp}
console> ntp server {self.rand_ntp()}

console> snmp version v3
console> snmp enable
console> snmp v3-user snmpv3admin auth SHA256 priv AES256

console> firewall rule add name "LAN-to-WAN-Web" src-zone LAN dst-zone WAN service HTTPS action accept log enable
console> firewall rule add name "Default-Deny" src-zone ANY dst-zone ANY service ANY action deny log enable
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Sophos XG — MISCONFIGURED — Sample {index}
console> system hostname {hn}
console> system admin timeout 0
console> system admin-password complexity disable
console> system admin-password min-length 1

console> interface Port1 ipaddress {self.rand_ip()} netmask 255.255.255.252
console> interface Port2 ipaddress {self.rand_ip()} netmask 255.255.255.0

console> service ssh enable
console> service telnet enable
console> service http-admin enable
console> service https-admin enable

console> log syslog remove all

console> snmp version v2c
console> snmp community public

console> firewall rule add name "Allow-All" src-zone ANY dst-zone ANY service ANY action accept log disable
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Sophos XG — EDGE CASE — Sample {index}
# UTM 9.x (legacy) config fragment
console> system hostname {self.rand_hostname()}
console> interface eth0 address {self.rand_ip()}/24
# Missing zone assignments, no firewall rules, partial setup
"""


# =============================================================================
# 7. SonicWall SonicOS
# =============================================================================
class SonicWallGenerator(ConfigGenerator):
    vendor = "SonicWall"
    product = "SonicWall"
    os_name = "SonicOS"
    os_version = "7.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "sonicwall_cli"
    vendor_dir_name = "sonicwall_sonicos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — SonicWall — SECURE — Sample {index}
hostname {hn}

interface X0
 ip {self.rand_ip()} netmask 255.255.255.0
 zone LAN
 management https ssh ping
 no management http telnet snmp
 no shutdown

interface X1
 ip {self.rand_ip()} netmask 255.255.255.252
 zone WAN
 no management
 no shutdown

interface X2
 ip {self.rand_ip()} netmask 255.255.255.0
 zone DMZ
 no management
 no shutdown

administration
 web-management https-port 4433
 no web-management http
 ssh enable
 ssh timeout 10
 no telnet
 password-complexity enable
 password-min-length 14
 admin-lockout enable
 admin-lockout-attempts 3
 admin-lockout-duration 300
 login-banner "WARNING: Authorized access only."

logging
 syslog-server {syslog} port 514
 syslog-facility local7
 logging-level informational
 log-admin-events enable
 log-connections enable

ntp
 ntp-server {ntp}
 ntp-enable

snmp
 version v3-only
 snmpv3-user admin auth-sha256 priv-aes256

access-rule
 from WAN to LAN action deny log enable
 from LAN to WAN service HTTPS action allow log enable
 from LAN to WAN service DNS action allow log enable
 default-action deny log enable
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — SonicWall — MISCONFIGURED — Sample {index}
hostname {hn}

interface X0
 ip {self.rand_ip()} netmask 255.255.255.0
 zone LAN
 management https ssh http telnet snmp ping
 no shutdown

interface X1
 ip {self.rand_ip()} netmask 255.255.255.252
 zone WAN
 management http
 no shutdown

administration
 web-management http
 telnet enable
 ssh timeout 0
 password-complexity disable
 admin-lockout disable

logging
 no syslog-server

snmp
 version v2c
 community public
 community private

access-rule
 from WAN to LAN action allow log disable
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — SonicWall — EDGE CASE — Sample {index}
# Gen5 SonicOS 5.x style config fragment
hostname {self.rand_hostname()}
interface X0 ip {self.rand_ip()} netmask 255.255.255.0 zone LAN
# No further config — imported from SonicOS 5.x backup
"""


# =============================================================================
# 8. WatchGuard Firebox
# =============================================================================
class WatchGuardGenerator(ConfigGenerator):
    vendor = "WatchGuard"
    product = "Firebox"
    os_name = "Fireware"
    os_version = "12.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "watchguard_cli"
    vendor_dir_name = "watchguard_firebox"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — WatchGuard Firebox — SECURE — Sample {index}
policy-type firebox

system
  hostname {hn}
  contact security-team@example.lab
  location Datacenter-A
  login-banner "WARNING: Authorized access only. Activity is logged."

interface
  external eth0 ip {self.rand_ip()}/30
  trusted eth1 ip {self.rand_ip()}/24
  optional eth2 ip {self.rand_ip()}/24

management
  https-port 8080
  ssh enable
  ssh-port 22
  no telnet
  no http
  session-timeout 10
  admin-lockout attempts 3 duration 300
  password-policy min-length 14 complexity enable

logging
  syslog-server {syslog} port 514
  log-level info
  log-admin-actions enable
  log-connections enable
  log-denied enable

ntp-server primary {ntp}
ntp-server secondary {self.rand_ntp()}
ntp-enable

snmp
  version v3
  snmpv3-user admin auth sha256 priv aes256
  no v2c-community

policy
  rule 1 from trusted to external service HTTPS action allow log enable
  rule 2 from trusted to external service DNS action allow log enable
  rule 999 from any to any service any action deny log enable
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — WatchGuard Firebox — MISCONFIGURED — Sample {index}
system
  hostname {hn}

interface
  external eth0 ip {self.rand_ip()}/30
  trusted eth1 ip {self.rand_ip()}/24

management
  http enable
  telnet enable
  session-timeout 0
  password-policy min-length 1 complexity disable

logging
  no syslog-server

snmp
  version v2c
  community public read-only
  community private read-write

policy
  rule 1 from any to any service any action allow log disable
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — WatchGuard Firebox — EDGE CASE — Sample {index}
# XML policy export fragment (Firebox System Manager)
system hostname {self.rand_hostname()}
# Mixed CLI and XML-style — partial export
# <policy name="allow-all"><from>any</from><to>any</to><action>allow</action></policy>
interface external eth0 ip {self.rand_ip()}/30
"""


# =============================================================================
# 9. Barracuda CloudGen
# =============================================================================
class BarracudaGenerator(ConfigGenerator):
    vendor = "Barracuda"
    product = "CloudGen Firewall"
    os_name = "Barracuda Firewall OS"
    os_version = "9.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "barracuda_cli"
    vendor_dir_name = "barracuda_cloudgen"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Barracuda CloudGen — SECURE — Sample {index}
set hostname {hn}
set domain example.lab

set interface eth0 ip {self.rand_ip()}/30 zone internet
set interface eth1 ip {self.rand_ip()}/24 zone trusted
set interface eth2 ip {self.rand_ip()}/24 zone dmz

set management ssh enable version 2
set management ssh timeout 10
set management https enable port 8443
set management telnet disable
set management http disable
set management login-banner "WARNING: Authorized access only."
set management lockout enable attempts 3 duration 300
set management password-policy min-length 14 complexity enable

set logging syslog server {syslog} port 514 protocol udp
set logging level informational
set logging admin-events enable

set ntp enable server {ntp}

set snmp version v3
set snmp v3-user admin auth sha256 priv aes256

set firewall rule 1 from trusted to internet service HTTPS action accept log enable
set firewall rule 2 from trusted to internet service DNS action accept log enable
set firewall rule 999 from any to any service any action deny log enable
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Barracuda CloudGen — MISCONFIGURED — Sample {index}
set hostname {hn}
set interface eth0 ip {self.rand_ip()}/30
set interface eth1 ip {self.rand_ip()}/24

set management telnet enable
set management http enable
set management lockout disable
set management password-policy min-length 1

set logging syslog disable
set ntp disable

set snmp version v2c community public

set firewall rule 1 from any to any service any action accept log disable
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Barracuda CloudGen — EDGE CASE — Sample {index}
# PAR file import fragment
set hostname {self.rand_hostname()}
set interface eth0 ip {self.rand_ip()}/24
# Incomplete — missing firewall rules, logging, authentication
"""


# =============================================================================
# 10. Forcepoint NGFW
# =============================================================================
class ForcepointGenerator(ConfigGenerator):
    vendor = "Forcepoint"
    product = "NGFW"
    os_name = "Forcepoint NGFW"
    os_version = "6.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "forcepoint_cli"
    vendor_dir_name = "forcepoint_ngfw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Forcepoint NGFW — SECURE — Sample {index}
system hostname {hn}
system domain example.lab
system management ssh enable
system management ssh version 2
system management https enable port 8443
system management telnet disable
system management http disable
system management session-timeout 10
system management lockout enable attempts 3 duration 300
system management password-policy min-length 14

interface 0 ip {self.rand_ip()}/30 zone External
interface 1 ip {self.rand_ip()}/24 zone Internal
interface 2 ip {self.rand_ip()}/24 zone DMZ

logging syslog server {self.rand_syslog()} port 514
logging level informational
logging admin-actions enable

ntp server {self.rand_ntp()} enable

snmp version v3 user admin auth sha256 priv aes256

policy rule 1 src Internal dst External service HTTPS action allow log yes
policy rule 2 src Internal dst External service DNS action allow log yes
policy rule default action deny log yes
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Forcepoint NGFW — MISCONFIGURED — Sample {index}
system hostname {hn}
system management telnet enable
system management http enable
system management lockout disable

interface 0 ip {self.rand_ip()}/30
interface 1 ip {self.rand_ip()}/24

logging syslog disable

snmp version v2c community public

policy rule 1 src any dst any service any action allow log no
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Forcepoint NGFW — EDGE CASE — Sample {index}
# SMC-exported policy fragment
system hostname {self.rand_hostname()}
# Policy defined in SMC — CLI shows references only
policy template "Standard-NGFW-Policy" applied
interface 0 ip {self.rand_ip()}/24
"""


# =============================================================================
# 11. F5 BIG-IP AFM
# =============================================================================
class F5BigIPGenerator(ConfigGenerator):
    vendor = "F5"
    product = "BIG-IP AFM"
    os_name = "TMOS"
    os_version = "17.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "f5_tmsh"
    vendor_dir_name = "f5_bigip_afm"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — F5 BIG-IP AFM — SECURE — Sample {index}
tmsh modify sys global-settings hostname {hn}.example.lab

tmsh modify sys httpd ssl-port 8443
tmsh modify sys httpd allow {{ {self.rand_ip()}/32 }}
tmsh modify sys httpd ssl-protocol "all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1"

tmsh modify sys sshd allow {{ {self.rand_ip()}/32 }}
tmsh modify sys sshd inactivity-timeout 600
tmsh modify sys sshd protocol-version 2
tmsh modify sys sshd login "disabled"

tmsh modify sys db systemauth.disablerootlogin value true

tmsh modify auth password-policy min-length 14
tmsh modify auth password-policy required-uppercase 1
tmsh modify auth password-policy required-lowercase 1
tmsh modify auth password-policy required-numeric 1
tmsh modify auth password-policy required-special 1
tmsh modify auth password-policy max-login-failures 3
tmsh modify auth password-policy lockout-duration 300

tmsh create auth radius-server RADIUS-PRIMARY {{ server {self.rand_radius()} secret {self.rand_psk()} }}
tmsh modify auth radius {{ servers replace-all-with {{ RADIUS-PRIMARY }} }}

tmsh modify sys syslog remote-servers replace-all-with {{ SYSLOG-PRIMARY {{ host {syslog} remote-port 514 }} }}
tmsh modify sys syslog auth-priv-from warning
tmsh modify sys syslog auth-priv-to emerg

tmsh modify sys ntp servers replace-all-with {{ {ntp} {self.rand_ntp()} }}
tmsh modify sys ntp timezone America/New_York

tmsh modify sys snmp allowed-addresses replace-all-with {{ {self.rand_ip()}/32 }}
tmsh modify sys snmp communities none
tmsh create sys snmp users snmpv3admin {{ auth-protocol sha256 privacy-protocol aes auth-password {self.rand_password()} privacy-password {self.rand_password()} }}

tmsh create security firewall policy DENY-ALL rules replace-all-with {{ default-deny {{ action reject log yes }} }}
tmsh create security firewall policy ALLOW-WEB rules replace-all-with {{ allow-https {{ action accept ip-protocol tcp destination {{ ports replace-all-with {{ 443 }} }} log yes }} }}

tmsh modify sys global-settings gui-setup disabled
tmsh modify cli global-settings service number
tmsh modify sys db ui.advisory.enabled value true
tmsh modify sys db ui.advisory.text value "WARNING: Authorized access only"
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — F5 BIG-IP AFM — MISCONFIGURED — Sample {index}
tmsh modify sys global-settings hostname {hn}.example.lab
tmsh modify sys httpd ssl-port 443
tmsh modify sys httpd allow {{ all }}
tmsh modify sys httpd ssl-protocol all

tmsh modify sys sshd allow {{ all }}
tmsh modify sys sshd inactivity-timeout 0
tmsh modify sys sshd protocol-version {{ 1 2 }}

tmsh modify auth password-policy min-length 1
tmsh modify auth password-policy max-login-failures 0

tmsh modify sys syslog remote-servers none

tmsh modify sys snmp communities replace-all-with {{ community-public {{ community-name public access ro }} }}

tmsh modify sys ntp servers none
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — F5 BIG-IP AFM — EDGE CASE — Sample {index}
# SCF (Single Configuration File) fragment
tmsh modify sys global-settings hostname {self.rand_hostname()}.example.lab
# iApp template references — resolved at runtime
tmsh modify sys application template /Common/f5.http
# Incomplete — no self-IP, no VLAN, no pool
"""


# =============================================================================
# 12. Huawei USG
# =============================================================================
class HuaweiUSGGenerator(ConfigGenerator):
    vendor = "Huawei"
    product = "USG"
    os_name = "VRP"
    os_version = "VRP8"
    device_type = "firewall"
    category = "firewall"
    config_format = "huawei_vrp_cli"
    vendor_dir_name = "huawei_usg"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Huawei USG — SECURE — Sample {index}
sysname {hn}
header login information "WARNING: Authorized access only. Activity is logged."

interface GigabitEthernet0/0/0
 ip address {self.rand_ip()} 255.255.255.252
 description WAN-Uplink
 undo shutdown

interface GigabitEthernet0/0/1
 ip address {self.rand_ip()} 255.255.255.0
 description LAN-Internal
 undo shutdown

interface GigabitEthernet0/0/2
 ip address {self.rand_ip()} 255.255.255.0
 description DMZ
 undo shutdown

firewall zone untrust
 add interface GigabitEthernet0/0/0

firewall zone trust
 add interface GigabitEthernet0/0/1

firewall zone dmz
 add interface GigabitEthernet0/0/2

stelnet server enable
ssh server-source -i GigabitEthernet0/0/1
ssh authentication-type default password
undo telnet server enable
undo telnet server-source all-interface

undo web-manager enable http
web-manager enable https
web-manager security ssl-version tlsv1.2

aaa
 authentication-scheme RADIUS-SCHEME
  authentication-mode radius local
 domain default
  authentication-scheme RADIUS-SCHEME
  radius-server RADIUS-TEMPLATE

radius-server template RADIUS-TEMPLATE
 radius-server authentication {self.rand_radius()} 1812
 radius-server shared-key cipher {self.rand_psk()}
 radius-server retransmit 3
 radius-server timeout 5

local-user admin password irreversible-cipher {self.rand_password()}
local-user admin privilege level 3
local-user admin service-type terminal ssh

user-security-policy
 password complexity enable
 password min-length 14
 password expire 90
 login-failed-times 3
 login-failed-timer block-timer 5 block-time 300

info-center enable
info-center loghost {syslog} channel loghost
info-center source default channel loghost log level informational

ntp-service unicast-server {ntp}
ntp-service authentication enable
ntp-service authentication-keyid 1 authentication-mode md5 cipher {self.rand_psk()}
ntp-service reliable authentication-keyid 1

snmp-agent sys-info version v3
snmp-agent usm-user v3 snmpv3admin authentication-mode sha cipher {self.rand_password()} privacy-mode aes256 cipher {self.rand_password()}
undo snmp-agent sys-info version v1 v2c

security-policy
 rule name TRUST-TO-UNTRUST-WEB
  source-zone trust
  destination-zone untrust
  action permit
  service https dns
  logging enable
 rule name DEFAULT-DENY
  source-zone any
  destination-zone any
  action deny
  logging enable

return
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Huawei USG — MISCONFIGURED — Sample {index}
sysname {hn}

interface GigabitEthernet0/0/0
 ip address {self.rand_ip()} 255.255.255.252
 undo shutdown

interface GigabitEthernet0/0/1
 ip address {self.rand_ip()} 255.255.255.0
 undo shutdown

telnet server enable
telnet server-source all-interface
web-manager enable http

local-user admin password simple admin123
local-user admin privilege level 3

user-security-policy
 password complexity disable
 password min-length 1

undo info-center enable
undo ntp-service unicast-server

snmp-agent sys-info version v2c
snmp-agent community read public
snmp-agent community write private

security-policy
 rule name ALLOW-ALL
  source-zone any
  destination-zone any
  action permit

return
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Huawei USG — EDGE CASE — Sample {index}
# Incomplete NGFW config — only interface setup
sysname {self.rand_hostname()}
interface GigabitEthernet0/0/0
 ip address {self.rand_ip()} 255.255.255.252
 undo shutdown
# No zones, no security-policy, no logging
return
"""


# =============================================================================
# 13. Hillstone StoneOS
# =============================================================================
class HillstoneGenerator(ConfigGenerator):
    vendor = "Hillstone"
    product = "StoneOS"
    os_name = "StoneOS"
    os_version = "5.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "hillstone_cli"
    vendor_dir_name = "hillstone_stoneos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Hillstone StoneOS — SECURE — Sample {index}
hostname {hn}

interface ethernet0/0
 zone untrust
 ip address {self.rand_ip()} 255.255.255.252

interface ethernet0/1
 zone trust
 ip address {self.rand_ip()} 255.255.255.0

interface ethernet0/2
 zone dmz
 ip address {self.rand_ip()} 255.255.255.0

admin-user admin password {self.rand_password()} encrypted privilege admin
admin service ssh enable
admin service ssh version v2
admin service telnet disable
admin service http disable
admin service https enable port 4443
admin session-timeout 10
admin lockout enable max-attempts 3 duration 300
admin password-policy min-length 14

syslog host {self.rand_syslog()} port 514 facility local7
syslog level informational

ntp server {self.rand_ntp()} prefer
ntp enable

snmp version v3
snmp v3-user admin auth sha256 priv aes256

policy id 1
 name TRUST-TO-UNTRUST-WEB
 from trust to untrust
 service https dns
 action permit
 log enable

policy id 999
 name DEFAULT-DENY
 from any to any
 service any
 action deny
 log enable
"""

    def generate_misconfigured(self, index: int) -> str:
        return f"""# GAACA Dataset — Hillstone StoneOS — MISCONFIGURED — Sample {index}
hostname {self.rand_hostname()}
interface ethernet0/0 zone untrust ip address {self.rand_ip()} 255.255.255.252
interface ethernet0/1 zone trust ip address {self.rand_ip()} 255.255.255.0
admin service telnet enable
admin service http enable
admin lockout disable
admin password-policy min-length 1
syslog disable
ntp disable
snmp version v2c community public
policy id 1 from any to any service any action permit log disable
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Hillstone StoneOS — EDGE CASE — Sample {index}
hostname {self.rand_hostname()}
interface ethernet0/0 ip address {self.rand_ip()} 255.255.255.252
# No zone assignment, no policies
"""


# =============================================================================
# 14. Zyxel USG
# =============================================================================
class ZyxelGenerator(ConfigGenerator):
    vendor = "Zyxel"
    product = "USG/ATP"
    os_name = "ZLD"
    os_version = "5.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "zyxel_cli"
    vendor_dir_name = "zyxel_usg"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Zyxel USG — SECURE — Sample {index}
hostname {hn}

interface wan1 ip address {self.rand_ip()} netmask 255.255.255.252 zone WAN
interface lan1 ip address {self.rand_ip()} netmask 255.255.255.0 zone LAN
interface dmz ip address {self.rand_ip()} netmask 255.255.255.0 zone DMZ

service-control ssh enable
service-control ssh zone LAN
service-control telnet disable
service-control http disable
service-control https enable port 4443 zone LAN

management session-timeout 10
management password-policy min-length 14 complexity enable
management lockout enable attempts 3 duration 300

logging syslog server {self.rand_syslog()} port 514
logging level informational

ntp server {self.rand_ntp()} enable

snmp agent version v3-only
snmp v3-user admin auth sha priv aes

firewall rule 1 from LAN to WAN service HTTPS action allow log enable
firewall rule 999 from any to any service any action deny log enable
"""

    def generate_misconfigured(self, index: int) -> str:
        return f"""# GAACA Dataset — Zyxel USG — MISCONFIGURED — Sample {index}
hostname {self.rand_hostname()}
interface wan1 ip address {self.rand_ip()} netmask 255.255.255.252
interface lan1 ip address {self.rand_ip()} netmask 255.255.255.0
service-control telnet enable
service-control http enable
management lockout disable
management password-policy min-length 1
logging syslog disable
ntp disable
snmp agent version v2c community public
firewall rule 1 from any to any service any action allow log disable
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Zyxel USG — EDGE CASE — Sample {index}
hostname {self.rand_hostname()}
interface wan1 ip address {self.rand_ip()} netmask 255.255.255.252
# ZLD firmware upgrade pending — partial config
"""


# =============================================================================
# 15. MikroTik RouterOS Firewall
# =============================================================================
class MikroTikFWGenerator(ConfigGenerator):
    vendor = "MikroTik"
    product = "RouterOS"
    os_name = "RouterOS"
    os_version = "7.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "mikrotik_rsc"
    vendor_dir_name = "mikrotik_routeros_fw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — MikroTik RouterOS Firewall — SECURE — Sample {index}
/system identity set name="{hn}"

/ip address
add address={self.rand_ip()}/30 interface=ether1 comment="WAN-Uplink"
add address={self.rand_ip()}/24 interface=ether2 comment="LAN-Internal"
add address={self.rand_ip()}/24 interface=ether3 comment="DMZ"

/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=yes
set www-ssl disabled=no certificate=https-cert tls-version=only-1.2
set ssh disabled=no port=22
set api disabled=yes
set api-ssl disabled=yes
set winbox disabled=yes

/ip ssh set strong-crypto=yes always-allow-password-login=no forwarding-enabled=no

/user set [find name=admin] password="{self.rand_password()}"
/user set [find name=admin] address={self.rand_ip()}/32

/system logging action
set remote target=remote remote={syslog} remote-port=514
/system logging
add topics=critical action=remote
add topics=error action=remote
add topics=warning action=remote
add topics=info action=remote

/system ntp client set enabled=yes
/system ntp client servers add address={ntp}

/snmp set enabled=yes
/snmp community remove [find name=public]
/snmp set trap-version=3

/ip firewall filter
add chain=input connection-state=established,related action=accept
add chain=input protocol=icmp action=accept
add chain=input src-address={self.rand_ip()}/32 protocol=tcp dst-port=22 action=accept comment="SSH-Management"
add chain=input src-address={self.rand_ip()}/32 protocol=tcp dst-port=443 action=accept comment="HTTPS-Management"
add chain=input action=drop comment="Default-Drop-Input"

add chain=forward connection-state=established,related action=accept
add chain=forward in-interface=ether2 out-interface=ether1 protocol=tcp dst-port=443 action=accept comment="LAN-HTTPS"
add chain=forward in-interface=ether2 out-interface=ether1 protocol=udp dst-port=53 action=accept comment="LAN-DNS"
add chain=forward action=drop comment="Default-Drop-Forward"

/tool bandwidth-server set enabled=no
/ip proxy set enabled=no
/ip socks set enabled=no
/ip upnp set enabled=no
/ip cloud set ddns-enabled=no
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — MikroTik RouterOS Firewall — MISCONFIGURED — Sample {index}
/system identity set name="{hn}"

/ip address
add address={self.rand_ip()}/30 interface=ether1
add address={self.rand_ip()}/24 interface=ether2

/ip service
set telnet disabled=no
set ftp disabled=no
set www disabled=no
set ssh disabled=no
set api disabled=no
set winbox disabled=no

/ip ssh set strong-crypto=no

/user set [find name=admin] password=""

/system logging action
# No remote logging configured

/system ntp client set enabled=no

/snmp set enabled=yes
/snmp community set [find name=public] read-access=yes write-access=yes

/ip firewall filter
add chain=input action=accept
add chain=forward action=accept

/tool bandwidth-server set enabled=yes
/ip proxy set enabled=yes
/ip socks set enabled=yes
/ip upnp set enabled=yes
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — MikroTik RouterOS Firewall — EDGE CASE — Sample {index}
# RouterOS 6.x syntax (some differences from 7.x)
/system identity set name="{self.rand_hostname()}"
/ip address add address={self.rand_ip()}/24 interface=ether1
/ip firewall filter
# Empty filter — no rules defined
/system ntp client set enabled=yes primary-ntp={self.rand_ntp()}
# RouterOS 6.x NTP syntax differs from 7.x
"""


# =============================================================================
# 16. Ubiquiti EdgeRouter Firewall
# =============================================================================
class UbiquitiFWGenerator(ConfigGenerator):
    vendor = "Ubiquiti"
    product = "EdgeRouter"
    os_name = "EdgeOS"
    os_version = "2.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "edgeos_cli"
    vendor_dir_name = "ubiquiti_edgerouter_fw"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Ubiquiti EdgeRouter — SECURE — Sample {index}
set system host-name {hn}
set system domain-name example.lab
set system login banner pre-login "WARNING: Authorized access only."

set interfaces ethernet eth0 address {self.rand_ip()}/30
set interfaces ethernet eth0 description WAN-Uplink
set interfaces ethernet eth1 address {self.rand_ip()}/24
set interfaces ethernet eth1 description LAN-Internal

set service ssh protocol-version v2
set service ssh disable-password-authentication
set service ssh port 22
delete service telnet
delete service gui listen-address 0.0.0.0

set system login user admin authentication plaintext-password {self.rand_password()}
set system login user admin level admin

set system syslog host {self.rand_syslog()} facility all level info

set system ntp server {self.rand_ntp()}

set firewall name WAN_IN default-action drop
set firewall name WAN_IN rule 1 action accept state established enable
set firewall name WAN_IN rule 1 action accept state related enable
set firewall name WAN_IN rule 999 action drop log enable

set firewall name LAN_OUT default-action drop
set firewall name LAN_OUT rule 1 action accept state established enable
set firewall name LAN_OUT rule 10 action accept protocol tcp destination port 443
set firewall name LAN_OUT rule 20 action accept protocol udp destination port 53

set interfaces ethernet eth0 firewall in name WAN_IN
set interfaces ethernet eth1 firewall out name LAN_OUT
"""

    def generate_misconfigured(self, index: int) -> str:
        return f"""# GAACA Dataset — Ubiquiti EdgeRouter — MISCONFIGURED — Sample {index}
set system host-name {self.rand_hostname()}
set interfaces ethernet eth0 address {self.rand_ip()}/30
set interfaces ethernet eth1 address {self.rand_ip()}/24
set service ssh protocol-version v1
set service telnet port 23
set service gui listen-address 0.0.0.0
set system login user admin authentication plaintext-password admin
# No firewall rules
# No syslog
# No NTP
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Ubiquiti EdgeRouter — EDGE CASE — Sample {index}
set system host-name {self.rand_hostname()}
set interfaces ethernet eth0 address {self.rand_ip()}/24
# config.boot fragment — incomplete
# Vyatta-era commands mixed with EdgeOS
"""


# =============================================================================
# 17. OPNsense
# =============================================================================
class OPNsenseGenerator(ConfigGenerator):
    vendor = "OPNsense"
    product = "OPNsense"
    os_name = "OPNsense"
    os_version = "24.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "opnsense_xml"
    vendor_dir_name = "opnsense"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""<?xml version="1.0"?>
<!-- GAACA Dataset — OPNsense — SECURE — Sample {index} -->
<opnsense>
  <system>
    <hostname>{hn}</hostname>
    <domain>example.lab</domain>
    <timezone>America/New_York</timezone>
    <ssh>
      <enabled>enabled</enabled>
      <port>22</port>
      <permitrootlogin>0</permitrootlogin>
      <passwordauth>0</passwordauth>
    </ssh>
    <webgui>
      <protocol>https</protocol>
      <port>4443</port>
      <ssl-certref>selfsigned</ssl-certref>
      <noantilockout>0</noantilockout>
    </webgui>
    <disableconsolemenu>1</disableconsolemenu>
    <user>
      <name>admin</name>
      <password>{self.rand_password()}</password>
      <scope>system</scope>
      <groupname>admins</groupname>
    </user>
  </system>
  <interfaces>
    <wan>
      <if>igb0</if>
      <ipaddr>{self.rand_ip()}</ipaddr>
      <subnet>30</subnet>
      <descr>WAN-Uplink</descr>
      <enable>1</enable>
    </wan>
    <lan>
      <if>igb1</if>
      <ipaddr>{self.rand_ip()}</ipaddr>
      <subnet>24</subnet>
      <descr>LAN-Internal</descr>
      <enable>1</enable>
    </lan>
    <opt1>
      <if>igb2</if>
      <ipaddr>{self.rand_ip()}</ipaddr>
      <subnet>24</subnet>
      <descr>DMZ</descr>
      <enable>1</enable>
    </opt1>
  </interfaces>
  <syslog>
    <enable>1</enable>
    <remoteserver>{syslog}</remoteserver>
    <remoteserver2></remoteserver2>
    <logall>1</logall>
  </syslog>
  <ntpd>
    <enable>1</enable>
    <prefer>{ntp}</prefer>
  </ntpd>
  <snmpd>
    <enable>0</enable>
  </snmpd>
  <filter>
    <rule>
      <type>pass</type>
      <interface>lan</interface>
      <protocol>tcp</protocol>
      <destination><port>443</port></destination>
      <descr>LAN-to-WAN-HTTPS</descr>
      <log>1</log>
    </rule>
    <rule>
      <type>block</type>
      <interface>wan</interface>
      <protocol>any</protocol>
      <descr>Default-Deny-WAN</descr>
      <log>1</log>
    </rule>
  </filter>
</opnsense>"""

    def generate_misconfigured(self, index: int) -> str:
        return f"""<?xml version="1.0"?>
<!-- GAACA Dataset — OPNsense — MISCONFIGURED — Sample {index} -->
<opnsense>
  <system>
    <hostname>{self.rand_hostname()}</hostname>
    <ssh>
      <enabled>enabled</enabled>
      <permitrootlogin>1</permitrootlogin>
      <passwordauth>1</passwordauth>
    </ssh>
    <webgui>
      <protocol>http</protocol>
      <port>80</port>
    </webgui>
    <user>
      <name>admin</name>
      <password>admin</password>
    </user>
  </system>
  <interfaces>
    <wan><if>igb0</if><ipaddr>{self.rand_ip()}</ipaddr><subnet>30</subnet><enable>1</enable></wan>
    <lan><if>igb1</if><ipaddr>{self.rand_ip()}</ipaddr><subnet>24</subnet><enable>1</enable></lan>
  </interfaces>
  <syslog><enable>0</enable></syslog>
  <ntpd><enable>0</enable></ntpd>
  <snmpd><enable>1</enable><community>public</community></snmpd>
  <filter>
    <rule><type>pass</type><interface>wan</interface><protocol>any</protocol><descr>Allow-All</descr><log>0</log></rule>
  </filter>
</opnsense>"""

    def generate_edge_case(self, index: int) -> str:
        return f"""<?xml version="1.0"?>
<!-- GAACA Dataset — OPNsense — EDGE CASE — Sample {index} -->
<!-- Partial config — system section only -->
<opnsense>
  <system>
    <hostname>{self.rand_hostname()}</hostname>
    <domain>example.lab</domain>
  </system>
  <!-- No interfaces, no filter rules -->
</opnsense>"""


# =============================================================================
# 18. pfSense
# =============================================================================
class PfSenseGenerator(ConfigGenerator):
    vendor = "Netgate"
    product = "pfSense"
    os_name = "pfSense"
    os_version = "2.7.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "pfsense_xml"
    vendor_dir_name = "pfsense"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""<?xml version="1.0"?>
<!-- GAACA Dataset — pfSense — SECURE — Sample {index} -->
<pfsense>
  <version>24.03</version>
  <system>
    <hostname>{hn}</hostname>
    <domain>example.lab</domain>
    <timezone>America/New_York</timezone>
    <ssh>
      <enable>enabled</enable>
      <port>22</port>
      <sshdkeyonly>enabled</sshdkeyonly>
    </ssh>
    <webgui>
      <protocol>https</protocol>
      <port>4443</port>
      <loginautocomplete>0</loginautocomplete>
      <noantilockout>0</noantilockout>
    </webgui>
  </system>
  <interfaces>
    <wan>
      <if>igb0</if>
      <ipaddr>{self.rand_ip()}</ipaddr>
      <subnet>30</subnet>
      <descr>WAN</descr>
      <enable></enable>
    </wan>
    <lan>
      <if>igb1</if>
      <ipaddr>{self.rand_ip()}</ipaddr>
      <subnet>24</subnet>
      <descr>LAN</descr>
      <enable></enable>
    </lan>
  </interfaces>
  <syslog>
    <enable>1</enable>
    <remoteserver>{syslog}</remoteserver>
    <logall>1</logall>
  </syslog>
  <ntpd>
    <enable>1</enable>
    <timeservers>{ntp}</timeservers>
  </ntpd>
  <filter>
    <rule>
      <type>pass</type>
      <interface>lan</interface>
      <protocol>tcp</protocol>
      <destination><port>443</port></destination>
      <descr>LAN HTTPS Out</descr>
      <log></log>
    </rule>
    <rule>
      <type>block</type>
      <interface>wan</interface>
      <protocol>any</protocol>
      <descr>Default Deny WAN</descr>
      <log></log>
    </rule>
  </filter>
</pfsense>"""

    def generate_misconfigured(self, index: int) -> str:
        return f"""<?xml version="1.0"?>
<!-- GAACA Dataset — pfSense — MISCONFIGURED — Sample {index} -->
<pfsense>
  <system>
    <hostname>{self.rand_hostname()}</hostname>
    <webgui><protocol>http</protocol><port>80</port></webgui>
    <ssh><enable>enabled</enable><sshdkeyonly>0</sshdkeyonly></ssh>
  </system>
  <interfaces>
    <wan><if>igb0</if><ipaddr>{self.rand_ip()}</ipaddr><subnet>30</subnet></wan>
    <lan><if>igb1</if><ipaddr>{self.rand_ip()}</ipaddr><subnet>24</subnet></lan>
  </interfaces>
  <syslog><enable>0</enable></syslog>
  <filter>
    <rule><type>pass</type><interface>wan</interface><protocol>any</protocol><descr>Allow All</descr></rule>
  </filter>
</pfsense>"""

    def generate_edge_case(self, index: int) -> str:
        return f"""<?xml version="1.0"?>
<!-- GAACA Dataset — pfSense — EDGE CASE — Sample {index} -->
<pfsense>
  <version>2.4.5</version>
  <system><hostname>{self.rand_hostname()}</hostname></system>
  <!-- Legacy 2.4.x config format — some tags differ from 2.7.x -->
</pfsense>"""


# =============================================================================
# 19. Sangfor NGAF
# =============================================================================
class SangforGenerator(ConfigGenerator):
    vendor = "Sangfor"
    product = "NGAF"
    os_name = "Sangfor NGAF"
    os_version = "8.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "sangfor_cli"
    vendor_dir_name = "sangfor_ngaf"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Sangfor NGAF — SECURE — Sample {index}
system hostname {hn}
system domain example.lab

interface eth0 ip {self.rand_ip()}/30 zone untrust
interface eth1 ip {self.rand_ip()}/24 zone trust
interface eth2 ip {self.rand_ip()}/24 zone dmz

management ssh enable version v2
management https enable port 4443
management telnet disable
management http disable
management session-timeout 10
management lockout enable attempts 3 duration 300
management password-policy min-length 14

logging syslog server {self.rand_syslog()} port 514
logging level informational

ntp server {self.rand_ntp()} enable

snmp version v3 user admin auth sha256 priv aes256

security-policy rule 1 from trust to untrust service HTTPS action permit log enable
security-policy rule 999 from any to any service any action deny log enable
"""

    def generate_misconfigured(self, index: int) -> str:
        return f"""# GAACA Dataset — Sangfor NGAF — MISCONFIGURED — Sample {index}
system hostname {self.rand_hostname()}
interface eth0 ip {self.rand_ip()}/30
interface eth1 ip {self.rand_ip()}/24
management telnet enable
management http enable
management lockout disable
logging syslog disable
snmp version v2c community public
security-policy rule 1 from any to any service any action permit log disable
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Sangfor NGAF — EDGE CASE — Sample {index}
system hostname {self.rand_hostname()}
interface eth0 ip {self.rand_ip()}/24
# Web console-only config — CLI not fully representative
"""


# =============================================================================
# 20. Kerio Control
# =============================================================================
class KerioControlGenerator(ConfigGenerator):
    vendor = "GFI/Kerio"
    product = "Kerio Control"
    os_name = "Kerio Control"
    os_version = "9.x"
    device_type = "firewall"
    category = "firewall"
    config_format = "kerio_conf"
    vendor_dir_name = "kerio_control"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Kerio Control — SECURE — Sample {index}
# Kerio Control uses XML-based configuration
<config>
  <system>
    <hostname>{hn}</hostname>
    <admin-port>4081</admin-port>
    <admin-protocol>https</admin-protocol>
    <ssh-enabled>true</ssh-enabled>
    <telnet-enabled>false</telnet-enabled>
    <session-timeout>600</session-timeout>
    <lockout-enabled>true</lockout-enabled>
    <lockout-attempts>3</lockout-attempts>
    <lockout-duration>300</lockout-duration>
  </system>
  <interfaces>
    <interface name="WAN" ip="{self.rand_ip()}" mask="255.255.255.252" zone="Internet"/>
    <interface name="LAN" ip="{self.rand_ip()}" mask="255.255.255.0" zone="Trusted"/>
  </interfaces>
  <logging>
    <syslog-server>{self.rand_syslog()}</syslog-server>
    <syslog-port>514</syslog-port>
    <log-level>info</log-level>
  </logging>
  <traffic-rules>
    <rule name="LAN-HTTPS" src="Trusted" dst="Internet" service="HTTPS" action="allow" log="true"/>
    <rule name="Default-Deny" src="any" dst="any" service="any" action="deny" log="true"/>
  </traffic-rules>
</config>"""

    def generate_misconfigured(self, index: int) -> str:
        return f"""# GAACA Dataset — Kerio Control — MISCONFIGURED — Sample {index}
<config>
  <system>
    <hostname>{self.rand_hostname()}</hostname>
    <admin-protocol>http</admin-protocol>
    <telnet-enabled>true</telnet-enabled>
    <session-timeout>0</session-timeout>
    <lockout-enabled>false</lockout-enabled>
  </system>
  <interfaces>
    <interface name="WAN" ip="{self.rand_ip()}" mask="255.255.255.252"/>
    <interface name="LAN" ip="{self.rand_ip()}" mask="255.255.255.0"/>
  </interfaces>
  <traffic-rules>
    <rule name="Allow-All" src="any" dst="any" service="any" action="allow" log="false"/>
  </traffic-rules>
</config>"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — Kerio Control — EDGE CASE — Sample {index}
<config>
  <system><hostname>{self.rand_hostname()}</hostname></system>
  <!-- Partial export — no traffic rules or interfaces -->
</config>"""


# =============================================================================
# 21. iptables
# =============================================================================
class IptablesGenerator(ConfigGenerator):
    vendor = "Linux"
    product = "iptables"
    os_name = "Linux"
    os_version = "kernel 5.x+"
    device_type = "firewall"
    category = "firewall"
    config_format = "iptables_rules"
    vendor_dir_name = "iptables"

    def generate_secure(self, index: int) -> str:
        mgmt_ip = self.rand_ip()
        syslog = self.rand_syslog()
        return f"""# GAACA Dataset — iptables — SECURE — Sample {index}
# Generated iptables-save format
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]

# Loopback
-A INPUT -i lo -j ACCEPT
-A OUTPUT -o lo -j ACCEPT

# Established connections
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# SSH from management only
-A INPUT -s {mgmt_ip}/32 -p tcp --dport 22 -m state --state NEW -j ACCEPT

# ICMP rate-limited
-A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s --limit-burst 4 -j ACCEPT

# Drop invalid packets
-A INPUT -m state --state INVALID -j DROP

# Log and drop everything else
-A INPUT -j LOG --log-prefix "INPUT-DROP: " --log-level 4
-A INPUT -j DROP

# Forward rules — LAN to WAN
-A FORWARD -i eth1 -o eth0 -p tcp --dport 443 -m state --state NEW -j ACCEPT
-A FORWARD -i eth1 -o eth0 -p udp --dport 53 -m state --state NEW -j ACCEPT
-A FORWARD -j LOG --log-prefix "FORWARD-DROP: " --log-level 4
-A FORWARD -j DROP

COMMIT

*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

# Masquerade LAN
-A POSTROUTING -o eth0 -s {self.rand_ip()}/24 -j MASQUERADE

COMMIT

*raw
:PREROUTING ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

# Drop TCP Christmas tree packets
-A PREROUTING -p tcp --tcp-flags ALL ALL -j DROP
# Drop null packets
-A PREROUTING -p tcp --tcp-flags ALL NONE -j DROP

COMMIT
"""

    def generate_misconfigured(self, index: int) -> str:
        return f"""# GAACA Dataset — iptables — MISCONFIGURED — Sample {index}
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

# No rules — default ACCEPT everything

COMMIT

*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

-A POSTROUTING -o eth0 -j MASQUERADE

COMMIT
"""

    def generate_edge_case(self, index: int) -> str:
        return f"""# GAACA Dataset — iptables — EDGE CASE — Sample {index}
# Mixed iptables and nftables syntax
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]

-A INPUT -i lo -j ACCEPT
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
# NOTE: This system also has nft rules active
# nft add rule inet filter input tcp dport 22 accept
-A INPUT -p tcp --dport 22 -j ACCEPT

# Conflicting: accept then drop SSH
-A INPUT -p tcp --dport 22 -j DROP

COMMIT
"""


# =============================================================================
# Registry of all firewall generators
# =============================================================================
FIREWALL_GENERATORS = [
    CiscoASAGenerator,
    FortinetFortiGateGenerator,
    PaloAltoPANOSGenerator,
    CheckPointGaiaGenerator,
    JuniperSRXGenerator,
    SophosXGGenerator,
    SonicWallGenerator,
    WatchGuardGenerator,
    BarracudaGenerator,
    ForcepointGenerator,
    F5BigIPGenerator,
    HuaweiUSGGenerator,
    HillstoneGenerator,
    ZyxelGenerator,
    MikroTikFWGenerator,
    UbiquitiFWGenerator,
    OPNsenseGenerator,
    PfSenseGenerator,
    SangforGenerator,
    KerioControlGenerator,
    IptablesGenerator,
]
