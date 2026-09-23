# GAACA Dataset — MikroTik CRS Switch — SECURE — Sample 13
/system identity set name="DIST-CLOUDROUTERSWITCH(CRS)-SYD-80"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set ssh disabled=no strong-crypto=yes
/user set admin password="T3st_P@ssw0rd_Lab!" group=full
/interface bridge add name=bridge1 vlan-filtering=yes protocol-mode=rstp
/interface bridge port add bridge=bridge1 interface=ether1 edge=yes bpdu-guard=yes
/interface bridge vlan add bridge=bridge1 tagged=sfp-sfpplus1 untagged=ether1 vlan-ids=3734
/system logging action add name=rem target=remote remote=198.51.100.11
/system logging add topics=system,info action=rem
/system ntp client set enabled=yes
/system ntp client servers add address=192.0.2.123
