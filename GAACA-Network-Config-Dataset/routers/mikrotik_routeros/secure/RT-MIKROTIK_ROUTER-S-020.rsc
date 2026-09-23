# GAACA Dataset — MikroTik RouterOS — SECURE — Sample 20
/system identity set name="CAMPUS-CLOUDCOREROUTER(CCR)-AMS-11"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=no certificate=none port=443
/ip service set ssh disabled=no port=22 strong-crypto=yes
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set winbox disabled=yes
/user set admin password="P@ssw0rd_PLACEHOLDER" group=full
/ip address add address=203.0.113.65/30 interface=ether1 comment="WAN"
/ip address add address=192.0.2.230/24 interface=ether2 comment="LAN"
/routing bgp template add name=default as=65475 router-id=203.0.113.238
/routing bgp connection add name=peer1 remote.address=198.51.100.107 remote.as=65479 template=default md5-key="P@ssw0rd_PLACEHOLDER"
/system logging action add name=syslog-remote target=remote remote=203.0.113.50
/system logging add topics=critical,error,warning,info action=syslog-remote
/system ntp client set enabled=yes
/system ntp client servers add address=192.0.2.123
/snmp set enabled=no
