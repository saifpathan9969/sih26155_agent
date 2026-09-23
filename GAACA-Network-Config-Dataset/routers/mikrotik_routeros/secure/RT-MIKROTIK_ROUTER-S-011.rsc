# GAACA Dataset — MikroTik RouterOS — SECURE — Sample 11
/system identity set name="ACCESS-CLOUDCOREROUTER(CCR)-LON-62"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=no certificate=none port=443
/ip service set ssh disabled=no port=22 strong-crypto=yes
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set winbox disabled=yes
/user set admin password="P@ssw0rd_PLACEHOLDER" group=full
/ip address add address=192.0.2.145/30 interface=ether1 comment="WAN"
/ip address add address=203.0.113.169/24 interface=ether2 comment="LAN"
/routing bgp template add name=default as=65201 router-id=192.0.2.50
/routing bgp connection add name=peer1 remote.address=198.51.100.209 remote.as=64720 template=default md5-key="P@ssw0rd_PLACEHOLDER"
/system logging action add name=syslog-remote target=remote remote=203.0.113.50
/system logging add topics=critical,error,warning,info action=syslog-remote
/system ntp client set enabled=yes
/system ntp client servers add address=192.0.2.123
/snmp set enabled=no
