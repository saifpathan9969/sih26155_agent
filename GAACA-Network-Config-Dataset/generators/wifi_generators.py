"""
GAACA Dataset — WiFi Configuration Generators
==============================================
20 vendor generators for enterprise wireless controller & AP configurations.
Each produces secure, misconfigured, and edge_case variants.
"""

from __future__ import annotations
import json
from generators.base import ConfigGenerator


# =============================================================================
# 1. Cisco Catalyst 9800 / AireOS WLC
# =============================================================================
class CiscoWLCGenerator(ConfigGenerator):
    vendor = "Cisco"
    product = "Catalyst 9800 WLC"
    os_name = "Cisco IOS-XE Wireless"
    os_version = "17.9"
    device_type = "wifi_controller"
    category = "wifi"
    config_format = "cisco_iosxe_cli"
    vendor_dir_name = "cisco_wlc"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        radius = self.rand_radius()
        psk = self.rand_psk()
        return f"""! GAACA Dataset — Cisco WLC — SECURE — Sample {index}
hostname {hn}
wlan Corporate-Secure 1 Corporate-Secure
 shutdown
 security wpa
 security wpa wpa2
 security wpa akm 802.1x
 security wpa akm sae
 security wpa wpa3
 security pmf mandatory
 security dot1x authentication-list RADIUS-DOT1X
 peer-to-peer-blocking drop
 no shutdown
!
aaa new-model
aaa group server radius RADIUS-SERVERS
 server name RAD-AUTH
!
radius server RAD-AUTH
 address ipv4 {radius} auth-port 1812 acct-port 1813
 key {psk}
!
wireless profile mesh MESH-PROFILE
 security psk {pwd}
!
ip ssh version 2
no ip http server
ip http secure-server
logging host {syslog}
ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco WLC — MISCONFIGURED — Sample {index}
hostname {hn}
wlan Open-Guest 2 Open-Guest
 security wpa none
 no security pmf
 no peer-to-peer-blocking
 no shutdown
!
ip http server
no ip http secure-server
snmp-server community public rw
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Cisco WLC — EDGE CASE — Sample {index}
hostname {hn}
wlan Broken-WLAN 3 Broken-WLAN
 security wpa akm 802.1x
 ! Missing radius dot1x server binding
"""


# =============================================================================
# 2. Cisco Meraki MR
# =============================================================================
class CiscoMerakiWiFiGenerator(ConfigGenerator):
    vendor = "Cisco Meraki"
    product = "Meraki MR56 / MR46"
    os_name = "Meraki Cloud OS"
    os_version = "29.x"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "json"
    vendor_dir_name = "cisco_meraki"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        radius = self.rand_radius()
        psk = self.rand_psk()
        cfg = {
            "name": hn,
            "ssids": [
                {
                    "number": 0,
                    "name": "Corp-WiFi",
                    "enabled": True,
                    "authMode": "8021x-radius",
                    "enterpriseAdminAccess": "access-disabled",
                    "encryptionMode": "wpa3-wpa2",
                    "wpaEncryptionMode": "WPA3 Enterprise",
                    "radiusServers": [{"host": radius, "port": 1812, "secret": psk}],
                    "radiusCoaEnabled": True,
                    "clientIsolation": True,
                    "minBitrate": 12
                }
            ],
            "firewallAndTrafficShaping": {
                "blockLanTraffic": True
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "name": hn,
            "ssids": [
                {
                    "number": 0,
                    "name": "OpenPublic",
                    "enabled": True,
                    "authMode": "open",
                    "encryptionMode": "wep",
                    "clientIsolation": False
                }
            ]
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "name": hn,
            "ssids": [
                {
                    "number": 1,
                    "name": "Ghost-SSID",
                    "enabled": False
                }
            ]
        }
        return json.dumps(cfg, indent=4)


# =============================================================================
# 3. Aruba Instant AP (IAP)
# =============================================================================
class ArubaInstantGenerator(ConfigGenerator):
    vendor = "Aruba / HPE"
    product = "Instant AP 515 / 535"
    os_name = "InstantOS"
    os_version = "8.10"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "aruba_instant_cli"
    vendor_dir_name = "aruba_instant"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Aruba Instant AP — SECURE — Sample {index}
hostname {hn}
wlan ssid-profile Corp-Secure
 enable
 type employee
 essid Corp-Secure
 opmode wpa3-sae-aes
 wpa-passphrase {pwd}
 mfp-mandatory
 client-isolation
 rf-band 5.0
rf dot11a-radio-profile
 am-enable
syslog-server {syslog}
ntp-server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Aruba Instant AP — MISCONFIGURED — Sample {index}
hostname {hn}
wlan ssid-profile Open-WiFi
 enable
 type guest
 essid Open-WiFi
 opmode opensystem
 no client-isolation
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Aruba Instant AP — EDGE CASE — Sample {index}
hostname {hn}
wlan ssid-profile Dead-SSID
 ! SSID profile defined without essid
"""


# =============================================================================
# 4. Juniper Mist
# =============================================================================
class JuniperMistGenerator(ConfigGenerator):
    vendor = "Juniper Mist"
    product = "Mist AP43 / AP45"
    os_name = "Mist Cloud OS"
    os_version = "v2"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "json"
    vendor_dir_name = "juniper_mist"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        psk = self.rand_psk()
        cfg = {
            "name": hn,
            "wlans": [
                {
                    "ssid": "Mist-Enterprise",
                    "enabled": True,
                    "auth": {
                        "type": "eap",
                        "pairwise": ["ccmp", "gcmp-256"],
                        "wpa3": True
                    },
                    "isolation": True,
                    "band": "5ghz"
                }
            ],
            "site_id": "site-101"
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "name": hn,
            "wlans": [
                {
                    "ssid": "Mist-Insecure",
                    "enabled": True,
                    "auth": {"type": "open"},
                    "isolation": False
                }
            ]
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "name": hn,
            "wlans": []
        }
        return json.dumps(cfg, indent=4)


# =============================================================================
# 5. Ruckus Unleashed
# =============================================================================
class RuckusUnleashedGenerator(ConfigGenerator):
    vendor = "Ruckus Networks"
    product = "Unleashed R650 / R750"
    os_name = "Unleashed OS"
    os_version = "200.12"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "ruckus_cli"
    vendor_dir_name = "ruckus_unleashed"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Ruckus Unleashed — SECURE — Sample {index}
system-name {hn}
wlan "Corp-Wireless"
 ssid "Corp-Wireless"
 encryption wpa3-personal
 passphrase {pwd}
 isolate-clients
 no wpa
 qos-directed-multicast
exit
syslog server {syslog}
ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruckus Unleashed — MISCONFIGURED — Sample {index}
system-name {hn}
wlan "Free-Wifi"
 ssid "Free-Wifi"
 encryption open
 no isolate-clients
exit
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruckus Unleashed — EDGE CASE — Sample {index}
system-name {hn}
wlan "Hidden-Bug"
 hide-ssid
 ! Hidden without encryption or key
exit
"""


# =============================================================================
# 6. Ubiquiti UniFi AP
# =============================================================================
class UbiquitiUniFiWiFiGenerator(ConfigGenerator):
    vendor = "Ubiquiti Networks"
    product = "UniFi U6 Enterprise / Pro"
    os_name = "UniFi OS"
    os_version = "6.5"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "ini"
    vendor_dir_name = "ubiquiti_unifi"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Ubiquiti UniFi AP — SECURE — Sample {index}
system.hostname={hn}
sshd.status=enabled
sshd.port=22
telnetd.status=disabled
wireless.1.ssid=CorpSecure
wireless.1.security=wpa3
wireless.1.wpa_mode=3
wireless.1.passphrase={pwd}
wireless.1.isolate=1
wireless.1.pmf=required
syslog.remote_ip={syslog}
ntp.server={ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Ubiquiti UniFi AP — MISCONFIGURED — Sample {index}
system.hostname={hn}
telnetd.status=enabled
wireless.1.ssid=PublicUnsecure
wireless.1.security=none
wireless.1.isolate=0
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Ubiquiti UniFi AP — EDGE CASE — Sample {index}
system.hostname={hn}
wireless.1.status=disabled
"""


# =============================================================================
# 7. Fortinet FortiAP
# =============================================================================
class FortinetFortiAPGenerator(ConfigGenerator):
    vendor = "Fortinet"
    product = "FortiAP 431F"
    os_name = "FortiOS Wireless"
    os_version = "7.2"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "fortios_cli"
    vendor_dir_name = "fortinet_fortiap"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""# GAACA Dataset — Fortinet FortiAP — SECURE — Sample {index}
config wireless-controller vap
    edit "Corp-VAP"
        set ssid "Corp-WiFi"
        set security wpa3-enterprise
        set pmf mandatory
        set intra-vap-privacy enable
        set schedule "always"
    next
end
config wireless-controller wtp-profile
    edit "FAP431F-SECURE"
        set ap-country US
    next
end
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Fortinet FortiAP — MISCONFIGURED — Sample {index}
config wireless-controller vap
    edit "Insecure-VAP"
        set ssid "Insecure-WiFi"
        set security open
        set intra-vap-privacy disable
    next
end
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Fortinet FortiAP — EDGE CASE — Sample {index}
config wireless-controller vap
    edit "Unbound-VAP"
    next
end
"""


# =============================================================================
# 8. Extreme WiNG
# =============================================================================
class ExtremeWiNGGenerator(ConfigGenerator):
    vendor = "Extreme Networks"
    product = "WiNG AP7632 / AP8533"
    os_name = "WiNG"
    os_version = "7.x"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "extreme_wing_cli"
    vendor_dir_name = "extreme_wing"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""! GAACA Dataset — Extreme WiNG — SECURE — Sample {index}
hostname {hn}
wlan CorpSecure
 ssid CorpSecure
 encryption-type ccmp
 authentication-type wpa3-sae
 wpa-wpa2-passphrase {pwd}
 protected-mgmt-frame mandatory
 client-client-communication disabled
!
logging host {syslog}
ntp server {ntp}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Extreme WiNG — MISCONFIGURED — Sample {index}
hostname {hn}
wlan OpenNet
 ssid OpenNet
 encryption-type none
 authentication-type none
 client-client-communication enabled
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Extreme WiNG — EDGE CASE — Sample {index}
hostname {hn}
radio 1
 ! radio enabled without assigned WLAN
"""


# =============================================================================
# 9. Huawei Wireless AC
# =============================================================================
class HuaweiACGenerator(ConfigGenerator):
    vendor = "Huawei"
    product = "AC6508 / AC6805"
    os_name = "VRP"
    os_version = "V200R021"
    device_type = "wifi_controller"
    category = "wifi"
    config_format = "huawei_vrp_cli"
    vendor_dir_name = "huawei_ac"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        ntp = self.rand_ntp()
        return f"""# GAACA Dataset — Huawei Wireless AC — SECURE — Sample {index}
sysname {hn}
wlan
 security-profile name sec-prof
  security wpa3 sae
  sae-password cipher {pwd}
 ssid-profile name corp-ssid
  ssid Corp-WLAN
 vap-profile name vap-corp
  service-vlan vlan-id 100
  ssid-profile corp-ssid
  security-profile sec-prof
  user-isolate enable
#
info-center loghost {syslog}
ntp-service unicast-server {ntp}
return
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Huawei Wireless AC — MISCONFIGURED — Sample {index}
sysname {hn}
wlan
 security-profile name open-prof
  security open
 vap-profile name vap-open
  ssid-profile open-ssid
  security-profile open-prof
  user-isolate disable
return
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Huawei Wireless AC — EDGE CASE — Sample {index}
sysname {hn}
wlan
 ap-group name empty-group
 ! AP group with no profiles
return
"""


# =============================================================================
# 10. TP-Link Omada EAP
# =============================================================================
class TPLinkOmadaWiFiGenerator(ConfigGenerator):
    vendor = "TP-Link"
    product = "Omada EAP660 HD / EAP670"
    os_name = "Omada OS"
    os_version = "v5"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "json"
    vendor_dir_name = "tplink_omada_wifi"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "name": hn,
            "wireless": {
                "ssid": "Omada-Secure",
                "security": "WPA3-Personal",
                "password": pwd,
                "pmf": "required",
                "guest_network": True,
                "isolate": True
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "name": hn,
            "wireless": {
                "ssid": "Omada-Open",
                "security": "None",
                "isolate": False
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "name": hn,
            "wireless": {
                "ssid": ""
            }
        }
        return json.dumps(cfg, indent=4)


# =============================================================================
# 11. D-Link WiFi AP
# =============================================================================
class DLinkWiFiGenerator(ConfigGenerator):
    vendor = "D-Link"
    product = "DAP-X2850 AP"
    os_name = "D-Link AP OS"
    os_version = "2.0"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "dlink_cli"
    vendor_dir_name = "dlink_wifi"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""# GAACA Dataset — D-Link WiFi AP — SECURE — Sample {index}
set system hostname {hn}
set wireless ssid 1 "DLink-Secure"
set wireless auth 1 wpa3-personal
set wireless passphrase 1 {pwd}
set wireless isolation 1 enable
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — D-Link WiFi AP — MISCONFIGURED — Sample {index}
set system hostname {hn}
set wireless ssid 1 "DLink-Open"
set wireless auth 1 open
set wireless isolation 1 disable
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — D-Link WiFi AP — EDGE CASE — Sample {index}
set system hostname {hn}
set wireless radio 1 disable
"""


# =============================================================================
# 12. Netgear WiFi AP
# =============================================================================
class NetgearWiFiGenerator(ConfigGenerator):
    vendor = "Netgear"
    product = "Insight WAX630"
    os_name = "Insight OS"
    os_version = "10.x"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "json"
    vendor_dir_name = "netgear_wifi"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "deviceName": hn,
            "ssids": [
                {
                    "name": "Netgear-Corp",
                    "security": "WPA3",
                    "passphrase": pwd,
                    "clientIsolation": True
                }
            ]
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "deviceName": hn,
            "ssids": [
                {
                    "name": "Netgear-Public",
                    "security": "NONE",
                    "clientIsolation": False
                }
            ]
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "deviceName": hn,
            "ssids": []
        }
        return json.dumps(cfg, indent=4)


# =============================================================================
# 13. MikroTik CAPsMAN
# =============================================================================
class MikroTikCAPsMANGenerator(ConfigGenerator):
    vendor = "MikroTik"
    product = "RouterOS CAPsMAN AP"
    os_name = "RouterOS"
    os_version = "v7.x"
    device_type = "wifi_controller"
    category = "wifi"
    config_format = "mikrotik_rsc"
    vendor_dir_name = "mikrotik_capsman"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""# GAACA Dataset — MikroTik CAPsMAN — SECURE — Sample {index}
/caps-man security add name=sec-prof authentication-types=wpa2-eap,wpa3-eap encryption=aes-ccm
/caps-man datapath add name=dp-secure client-to-client-forwarding=no local-forwarding=no
/caps-man configuration add name=cfg-secure ssid=MikroTik-Enterprise security=sec-prof datapath=dp-secure
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — MikroTik CAPsMAN — MISCONFIGURED — Sample {index}
/caps-man security add name=sec-open authentication-types="" encryption=""
/caps-man datapath add name=dp-open client-to-client-forwarding=yes
/caps-man configuration add name=cfg-open ssid=FreeWiFi security=sec-open datapath=dp-open
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — MikroTik CAPsMAN — EDGE CASE — Sample {index}
/caps-man interface add name=cap1
! CAP interface with no configuration applied
"""


# =============================================================================
# 14. Cambium cnMaestro
# =============================================================================
class CambiumCnMaestroGenerator(ConfigGenerator):
    vendor = "Cambium Networks"
    product = "cnPilot XV2-2 / cnMaestro"
    os_name = "cnOS"
    os_version = "6.x"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "json"
    vendor_dir_name = "cambium_cnmaestro"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "device": hn,
            "wlan": {
                "ssid": "Cambium-Corp",
                "security": "wpa3-enterprise",
                "pmf": "mandatory",
                "isolate": True
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "device": hn,
            "wlan": {
                "ssid": "Cambium-Guest",
                "security": "open",
                "isolate": False
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"device": hn, "wlan": {}}
        return json.dumps(cfg, indent=4)


# =============================================================================
# 15. Grandstream GWN
# =============================================================================
class GrandstreamGWNGenerator(ConfigGenerator):
    vendor = "Grandstream"
    product = "GWN7660 / GWN7664"
    os_name = "GWN OS"
    os_version = "1.0.x"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "xml"
    vendor_dir_name = "grandstream_gwn"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Grandstream GWN — SECURE — Sample {index} -->
<config version="1.0">
  <hostname>{hn}</hostname>
  <ssid name="GWN-Secure">
    <security>WPA3-SAE</security>
    <passphrase>{pwd}</passphrase>
    <client_isolation>1</client_isolation>
  </ssid>
</config>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Grandstream GWN — MISCONFIGURED — Sample {index} -->
<config version="1.0">
  <hostname>{hn}</hostname>
  <ssid name="GWN-Open">
    <security>Open</security>
    <client_isolation>0</client_isolation>
  </ssid>
</config>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Grandstream GWN — EDGE CASE — Sample {index} -->
<config version="1.0">
  <hostname>{hn}</hostname>
</config>
"""


# =============================================================================
# 16. EnGenius Cloud AP
# =============================================================================
class EnGeniusCloudGenerator(ConfigGenerator):
    vendor = "EnGenius"
    product = "Cloud ECW230"
    os_name = "EnGenius Cloud"
    os_version = "v3"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "json"
    vendor_dir_name = "engenius_cloud"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "device": hn,
            "ssid_profile": {
                "name": "EnGenius-Sec",
                "auth_type": "WPA3-Enterprise",
                "isolation": True
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "device": hn,
            "ssid_profile": {
                "name": "EnGenius-Open",
                "auth_type": "Open",
                "isolation": False
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"device": hn, "ssid_profile": {}}
        return json.dumps(cfg, indent=4)


# =============================================================================
# 17. Ruijie RG-AP Wireless
# =============================================================================
class RuijieRGWiFiGenerator(ConfigGenerator):
    vendor = "Ruijie Networks"
    product = "RG-AP820-L AP"
    os_name = "RGOS Wireless"
    os_version = "11.x"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "ruijie_rgos_cli"
    vendor_dir_name = "ruijie_rg_wifi"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""! GAACA Dataset — Ruijie WiFi — SECURE — Sample {index}
hostname {hn}
wlan-config 1 Corp-Ruijie
 security wpa3-sae
 sae-password {pwd}
 sta-isolation
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruijie WiFi — MISCONFIGURED — Sample {index}
hostname {hn}
wlan-config 1 Free-Ruijie
 security open
 no sta-isolation
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""! GAACA Dataset — Ruijie WiFi — EDGE CASE — Sample {index}
hostname {hn}
wlan-config 1 Ghost-Ruijie
 ! no security or sta config
"""


# =============================================================================
# 18. Zyxel Nebula AP
# =============================================================================
class ZyxelNebulaGenerator(ConfigGenerator):
    vendor = "Zyxel"
    product = "Nebula NWA110AX"
    os_name = "Nebula OS"
    os_version = "6.x"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "json"
    vendor_dir_name = "zyxel_nebula"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "hostname": hn,
            "ssid": "Zyxel-Corp",
            "security": "WPA3",
            "key": pwd,
            "intra_bss_traffic_blocking": True
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "hostname": hn,
            "ssid": "Zyxel-Public",
            "security": "NONE",
            "intra_bss_traffic_blocking": False
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"hostname": hn}
        return json.dumps(cfg, indent=4)


# =============================================================================
# 19. DrayTek Vigor AP
# =============================================================================
class DrayTekVigorWiFiGenerator(ConfigGenerator):
    vendor = "DrayTek"
    product = "VigorAP 1060C"
    os_name = "VigorOS"
    os_version = "1.4"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "cisco_ios_cli"
    vendor_dir_name = "draytek_vigor"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""# GAACA Dataset — DrayTek Vigor AP — SECURE — Sample {index}
sys hostname {hn}
wl general enable
wl ssid 1 CorpVigor
wl auth 1 wpa3-personal
wl psk 1 {pwd}
wl isolate 1 enable
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — DrayTek Vigor AP — MISCONFIGURED — Sample {index}
sys hostname {hn}
wl general enable
wl ssid 1 OpenVigor
wl auth 1 open
wl isolate 1 disable
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — DrayTek Vigor AP — EDGE CASE — Sample {index}
sys hostname {hn}
wl general disable
"""


# =============================================================================
# 20. Sophos Wireless AP
# =============================================================================
class SophosWiFiGenerator(ConfigGenerator):
    vendor = "Sophos"
    product = "APX 320 / 740"
    os_name = "Sophos Central Wireless"
    os_version = "v2"
    device_type = "wifi_access_point"
    category = "wifi"
    config_format = "json"
    vendor_dir_name = "sophos_wifi"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "device": hn,
            "wireless_networks": [
                {
                    "ssid": "Sophos-Secure",
                    "encryption": "WPA3",
                    "passphrase": pwd,
                    "client_isolation": True
                }
            ]
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "device": hn,
            "wireless_networks": [
                {
                    "ssid": "Sophos-Open",
                    "encryption": "None",
                    "client_isolation": False
                }
            ]
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"device": hn, "wireless_networks": []}
        return json.dumps(cfg, indent=4)


# =============================================================================
# Registry of all WiFi generators
# =============================================================================
WIFI_GENERATORS = [
    CiscoWLCGenerator,
    CiscoMerakiWiFiGenerator,
    ArubaInstantGenerator,
    JuniperMistGenerator,
    RuckusUnleashedGenerator,
    UbiquitiUniFiWiFiGenerator,
    FortinetFortiAPGenerator,
    ExtremeWiNGGenerator,
    HuaweiACGenerator,
    TPLinkOmadaWiFiGenerator,
    DLinkWiFiGenerator,
    NetgearWiFiGenerator,
    MikroTikCAPsMANGenerator,
    CambiumCnMaestroGenerator,
    GrandstreamGWNGenerator,
    EnGeniusCloudGenerator,
    RuijieRGWiFiGenerator,
    ZyxelNebulaGenerator,
    DrayTekVigorWiFiGenerator,
    SophosWiFiGenerator,
]
