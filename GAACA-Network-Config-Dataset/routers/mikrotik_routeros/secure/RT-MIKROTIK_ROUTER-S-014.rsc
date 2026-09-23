# GAACA Dataset — MikroTik RouterOS — SECURE — Sample 14
/system identity set name="BR-CLOUDCOREROUTER(CCR)-DAL-71"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=no certificate=none port=443
/ip service set ssh disabled=no port=22 strong-crypto=yes
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set winbox disabled=yes
/user set admin password="REDACTED_ADMIN_PASS" group=full
/ip address add address=203.0.113.200/30 interface=ether1 comment="WAN"
/ip address add address=203.0.113.150/24 interface=ether2 comment="LAN"
/routing bgp template add name=default as=65188 router-id=198.51.100.98
/routing bgp connection add name=peer1 remote.address=203.0.113.139 remote.as=64579 template=default md5-key="REDACTED_ADMIN_PASS"
/system logging action add name=syslog-remote target=remote remote=198.51.100.11
/system logging add topics=critical,error,warning,info action=syslog-remote
/system ntp client set enabled=yes
/system ntp client servers add address=198.51.100.123
/snmp set enabled=no
