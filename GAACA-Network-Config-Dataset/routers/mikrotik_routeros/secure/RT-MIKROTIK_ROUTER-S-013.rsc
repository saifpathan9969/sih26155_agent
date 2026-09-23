# GAACA Dataset — MikroTik RouterOS — SECURE — Sample 13
/system identity set name="DIST-CLOUDCOREROUTER(CCR)-SYD-80"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=no certificate=none port=443
/ip service set ssh disabled=no port=22 strong-crypto=yes
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set winbox disabled=yes
/user set admin password="T3st_P@ssw0rd_Lab!" group=full
/ip address add address=192.0.2.28/30 interface=ether1 comment="WAN"
/ip address add address=203.0.113.239/24 interface=ether2 comment="LAN"
/routing bgp template add name=default as=64653 router-id=192.0.2.227
/routing bgp connection add name=peer1 remote.address=192.0.2.242 remote.as=64532 template=default md5-key="T3st_P@ssw0rd_Lab!"
/system logging action add name=syslog-remote target=remote remote=198.51.100.11
/system logging add topics=critical,error,warning,info action=syslog-remote
/system ntp client set enabled=yes
/system ntp client servers add address=192.0.2.123
/snmp set enabled=no
