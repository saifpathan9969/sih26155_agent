# GAACA Dataset — MikroTik RouterOS Firewall — SECURE — Sample 11
/system identity set name="ACCESS-ROUTEROS-LON-62"

/ip address
add address=203.0.113.139/30 interface=ether1 comment="WAN-Uplink"
add address=192.0.2.145/24 interface=ether2 comment="LAN-Internal"
add address=203.0.113.169/24 interface=ether3 comment="DMZ"

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

/user set [find name=admin] password="P@ssw0rd_PLACEHOLDER"
/user set [find name=admin] address=192.0.2.254/32

/system logging action
set remote target=remote remote=203.0.113.50 remote-port=514
/system logging
add topics=critical action=remote
add topics=error action=remote
add topics=warning action=remote
add topics=info action=remote

/system ntp client set enabled=yes
/system ntp client servers add address=198.51.100.123

/snmp set enabled=yes
/snmp community remove [find name=public]
/snmp set trap-version=3

/ip firewall filter
add chain=input connection-state=established,related action=accept
add chain=input protocol=icmp action=accept
add chain=input src-address=198.51.100.209/32 protocol=tcp dst-port=22 action=accept comment="SSH-Management"
add chain=input src-address=192.0.2.19/32 protocol=tcp dst-port=443 action=accept comment="HTTPS-Management"
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
