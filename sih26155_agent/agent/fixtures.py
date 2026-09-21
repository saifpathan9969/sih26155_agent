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
}
