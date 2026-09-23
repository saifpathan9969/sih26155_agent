# GAACA Dataset — MikroTik RouterOS Firewall — EDGE CASE — Sample 8
# RouterOS 6.x syntax (some differences from 7.x)
/system identity set name="CORE-ROUTEROS-AMS-98"
/ip address add address=192.0.2.172/24 interface=ether1
/ip firewall filter
# Empty filter — no rules defined
/system ntp client set enabled=yes primary-ntp=198.51.100.123
# RouterOS 6.x NTP syntax differs from 7.x
