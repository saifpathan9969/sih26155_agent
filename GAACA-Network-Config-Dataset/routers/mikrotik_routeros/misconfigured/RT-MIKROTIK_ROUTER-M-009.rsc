# GAACA Dataset — MikroTik RouterOS — MISCONFIGURED — Sample 9
/system identity set name="DIST-CLOUDCOREROUTER(CCR)-PAR-74"
/ip service set telnet disabled=no port=23
/ip service set www disabled=no port=80
/ip service set api disabled=no port=8728
/ip service set winbox disabled=no
/user set admin password="" group=full
/snmp set enabled=yes
/snmp community set [ find default=yes ] name=public write-access=yes
/ip address add address=203.0.113.223/24 interface=ether1
