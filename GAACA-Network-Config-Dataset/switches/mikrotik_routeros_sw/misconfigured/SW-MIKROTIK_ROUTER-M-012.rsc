# GAACA Dataset — MikroTik CRS Switch — MISCONFIGURED — Sample 12
/system identity set name="DMZ-CLOUDROUTERSWITCH(CRS)-NYC-20"
/ip service set telnet disabled=no
/ip service set www disabled=no
/user set admin password="" group=full
/interface bridge add name=bridge1 vlan-filtering=no
/snmp set enabled=yes
/snmp community set [ find default=yes ] name=public write-access=yes
