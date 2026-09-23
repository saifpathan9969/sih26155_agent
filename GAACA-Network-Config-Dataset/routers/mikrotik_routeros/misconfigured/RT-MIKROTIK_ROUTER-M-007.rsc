# GAACA Dataset — MikroTik RouterOS — MISCONFIGURED — Sample 7
/system identity set name="REMOTE-CLOUDCOREROUTER(CCR)-SFO-60"
/ip service set telnet disabled=no port=23
/ip service set www disabled=no port=80
/ip service set api disabled=no port=8728
/ip service set winbox disabled=no
/user set admin password="" group=full
/snmp set enabled=yes
/snmp community set [ find default=yes ] name=public write-access=yes
/ip address add address=198.51.100.6/24 interface=ether1
