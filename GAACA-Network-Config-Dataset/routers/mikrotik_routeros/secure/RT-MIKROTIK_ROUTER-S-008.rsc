# GAACA Dataset — MikroTik RouterOS — SECURE — Sample 8
/system identity set name="DMZ-CLOUDCOREROUTER(CCR)-SFO-41"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=no certificate=none port=443
/ip service set ssh disabled=no port=22 strong-crypto=yes
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set winbox disabled=yes
/user set admin password="T3st_P@ssw0rd_Lab!" group=full
/ip address add address=203.0.113.233/30 interface=ether1 comment="WAN"
/ip address add address=198.51.100.213/24 interface=ether2 comment="LAN"
/routing bgp template add name=default as=64554 router-id=203.0.113.101
/routing bgp connection add name=peer1 remote.address=198.51.100.251 remote.as=64697 template=default md5-key="T3st_P@ssw0rd_Lab!"
/system logging action add name=syslog-remote target=remote remote=198.51.100.11
/system logging add topics=critical,error,warning,info action=syslog-remote
/system ntp client set enabled=yes
/system ntp client servers add address=198.51.100.123
/snmp set enabled=no
