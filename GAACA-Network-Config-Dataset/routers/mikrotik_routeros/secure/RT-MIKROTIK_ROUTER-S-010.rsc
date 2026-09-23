# GAACA Dataset — MikroTik RouterOS — SECURE — Sample 10
/system identity set name="DIST-CLOUDCOREROUTER(CCR)-SIN-19"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=no certificate=none port=443
/ip service set ssh disabled=no port=22 strong-crypto=yes
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set winbox disabled=yes
/user set admin password="Ch@ng3M3_N0w_2026!" group=full
/ip address add address=192.0.2.89/30 interface=ether1 comment="WAN"
/ip address add address=198.51.100.167/24 interface=ether2 comment="LAN"
/routing bgp template add name=default as=65382 router-id=198.51.100.137
/routing bgp connection add name=peer1 remote.address=203.0.113.51 remote.as=65172 template=default md5-key="Ch@ng3M3_N0w_2026!"
/system logging action add name=syslog-remote target=remote remote=198.51.100.10
/system logging add topics=critical,error,warning,info action=syslog-remote
/system ntp client set enabled=yes
/system ntp client servers add address=192.0.2.123
/snmp set enabled=no
