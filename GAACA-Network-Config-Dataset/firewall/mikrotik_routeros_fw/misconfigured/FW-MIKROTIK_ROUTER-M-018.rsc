# GAACA Dataset — MikroTik RouterOS Firewall — MISCONFIGURED — Sample 18
/system identity set name="STAGING-ROUTEROS-BER-62"

/ip address
add address=192.0.2.62/30 interface=ether1
add address=198.51.100.200/24 interface=ether2

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
