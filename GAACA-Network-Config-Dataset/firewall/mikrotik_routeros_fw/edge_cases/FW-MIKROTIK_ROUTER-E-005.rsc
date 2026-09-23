# GAACA Dataset — MikroTik RouterOS Firewall — EDGE CASE — Sample 5
# RouterOS 6.x syntax (some differences from 7.x)
/system identity set name="BR-ROUTEROS-TKY-94"
/ip address add address=198.51.100.178/24 interface=ether1
/ip firewall filter
# Empty filter — no rules defined
/system ntp client set enabled=yes primary-ntp=203.0.113.123
# RouterOS 6.x NTP syntax differs from 7.x
