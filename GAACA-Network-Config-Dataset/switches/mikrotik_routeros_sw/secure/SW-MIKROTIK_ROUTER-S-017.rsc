# GAACA Dataset — MikroTik CRS Switch — SECURE — Sample 17
/system identity set name="CORE-CLOUDROUTERSWITCH(CRS)-DXB-68"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set ssh disabled=no strong-crypto=yes
/user set admin password="Ch@ng3M3_N0w_2026!" group=full
/interface bridge add name=bridge1 vlan-filtering=yes protocol-mode=rstp
/interface bridge port add bridge=bridge1 interface=ether1 edge=yes bpdu-guard=yes
/interface bridge vlan add bridge=bridge1 tagged=sfp-sfpplus1 untagged=ether1 vlan-ids=1615
/system logging action add name=rem target=remote remote=203.0.113.50
/system logging add topics=system,info action=rem
/system ntp client set enabled=yes
/system ntp client servers add address=203.0.113.123
