# GAACA Dataset — MikroTik CRS Switch — MISCONFIGURED — Sample 15
/system identity set name="BR-CLOUDROUTERSWITCH(CRS)-FRA-69"
/ip service set telnet disabled=no
/ip service set www disabled=no
/user set admin password="" group=full
/interface bridge add name=bridge1 vlan-filtering=no
/snmp set enabled=yes
/snmp community set [ find default=yes ] name=public write-access=yes
