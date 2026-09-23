# GAACA Dataset — MikroTik CRS Switch — SECURE — Sample 2
/system identity set name="PROD-CLOUDROUTERSWITCH(CRS)-BER-64"
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set ssh disabled=no strong-crypto=yes
/user set admin password="REDACTED_ADMIN_PASS" group=full
/interface bridge add name=bridge1 vlan-filtering=yes protocol-mode=rstp
/interface bridge port add bridge=bridge1 interface=ether1 edge=yes bpdu-guard=yes
/interface bridge vlan add bridge=bridge1 tagged=sfp-sfpplus1 untagged=ether1 vlan-ids=2912
/system logging action add name=rem target=remote remote=198.51.100.10
/system logging add topics=system,info action=rem
/system ntp client set enabled=yes
/system ntp client servers add address=203.0.113.123
