# GAACA Dataset — MikroTik RouterOS — MISCONFIGURED — Sample 10
/system identity set name="REMOTE-CLOUDCOREROUTER(CCR)-MUM-15"
/ip service set telnet disabled=no port=23
/ip service set www disabled=no port=80
/ip service set api disabled=no port=8728
/ip service set winbox disabled=no
/user set admin password="" group=full
/snmp set enabled=yes
/snmp community set [ find default=yes ] name=public write-access=yes
/ip address add address=192.0.2.170/24 interface=ether1
