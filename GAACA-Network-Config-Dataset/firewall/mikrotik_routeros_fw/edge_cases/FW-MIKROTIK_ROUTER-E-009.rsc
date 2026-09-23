# GAACA Dataset — MikroTik RouterOS Firewall — EDGE CASE — Sample 9
# RouterOS 6.x syntax (some differences from 7.x)
/system identity set name="PROD-ROUTEROS-FRA-20"
/ip address add address=203.0.113.68/24 interface=ether1
/ip firewall filter
# Empty filter — no rules defined
/system ntp client set enabled=yes primary-ntp=203.0.113.123
# RouterOS 6.x NTP syntax differs from 7.x
