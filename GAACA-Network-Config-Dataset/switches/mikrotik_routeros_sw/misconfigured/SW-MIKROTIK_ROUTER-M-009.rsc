# GAACA Dataset — MikroTik CRS Switch — MISCONFIGURED — Sample 9
/system identity set name="DIST-CLOUDROUTERSWITCH(CRS)-PAR-74"
/ip service set telnet disabled=no
/ip service set www disabled=no
/user set admin password="" group=full
/interface bridge add name=bridge1 vlan-filtering=no
/snmp set enabled=yes
/snmp community set [ find default=yes ] name=public write-access=yes
