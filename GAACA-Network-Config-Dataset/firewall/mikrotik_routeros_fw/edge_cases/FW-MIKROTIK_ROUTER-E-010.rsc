# GAACA Dataset — MikroTik RouterOS Firewall — EDGE CASE — Sample 10
# RouterOS 6.x syntax (some differences from 7.x)
/system identity set name="HQ-ROUTEROS-AMS-46"
/ip address add address=198.51.100.179/24 interface=ether1
/ip firewall filter
# Empty filter — no rules defined
/system ntp client set enabled=yes primary-ntp=192.0.2.123
# RouterOS 6.x NTP syntax differs from 7.x
