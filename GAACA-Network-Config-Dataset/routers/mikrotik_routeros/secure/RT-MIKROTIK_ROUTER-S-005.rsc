# GAACA Dataset — MikroTik RouterOS — SECURE — Sample 5
/system identity set name="WAN-CLOUDCOREROUTER(CCR)-MUM-44"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=no certificate=none port=443
/ip service set ssh disabled=no port=22 strong-crypto=yes
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set winbox disabled=yes
/user set admin password="S3cur3_D3m0_P@ss!" group=full
/ip address add address=198.51.100.143/30 interface=ether1 comment="WAN"
/ip address add address=192.0.2.3/24 interface=ether2 comment="LAN"
/routing bgp template add name=default as=65232 router-id=192.0.2.189
/routing bgp connection add name=peer1 remote.address=198.51.100.223 remote.as=64997 template=default md5-key="S3cur3_D3m0_P@ss!"
/system logging action add name=syslog-remote target=remote remote=198.51.100.11
/system logging add topics=critical,error,warning,info action=syslog-remote
/system ntp client set enabled=yes
/system ntp client servers add address=198.51.100.123
/snmp set enabled=no
