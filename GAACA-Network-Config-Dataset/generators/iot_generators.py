"""
GAACA Dataset — IoT Configuration Generators
============================================
25 vendor generators for Industrial PLCs, IP Cameras, IoT Gateways,
and Smart IoT Devices. Each produces secure, misconfigured, and edge_case variants.
"""

from __future__ import annotations
import json
from generators.base import ConfigGenerator


# =============================================================================
# INDUSTRIAL PLCs (12)
# =============================================================================

# 1. Siemens PLC (S7-1200 / S7-1500)
class SiemensPLCGenerator(ConfigGenerator):
    vendor = "Siemens"
    product = "SIMATIC S7-1500 / S7-1200"
    os_name = "SIMATIC Firmware"
    os_version = "V2.9"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/siemens_plc"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        ntp = self.rand_ntp()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Siemens S7 PLC — SECURE — Sample {index} -->
<DeviceConfiguration version="2.9">
  <Device name="{hn}" type="CPU 1516-3 PN/DP">
    <Security>
      <ProtectionLevel>AccessProtectionFullWithPassword</ProtectionLevel>
      <PasswordEncrypted>{pwd}</PasswordEncrypted>
      <SecurePGPCCommunication>Enabled</SecurePGPCCommunication>
      <TlsVersion min="1.3" max="1.3"/>
      <CertificateStore validation="Strict"/>
      <WebserverProtection enabled="true" requireHttps="true"/>
      <PutGetCommunication enabled="false"/>
    </Security>
    <Network>
      <Interface id="PROFINET_1" ip="{self.rand_ip()}" subnet="255.255.255.0"/>
      <NTPClient enabled="true" server="{ntp}"/>
    </Network>
  </Device>
</DeviceConfiguration>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Siemens S7 PLC — MISCONFIGURED — Sample {index} -->
<DeviceConfiguration version="2.5">
  <Device name="{hn}" type="CPU 1516-3 PN/DP">
    <Security>
      <ProtectionLevel>NoProtection</ProtectionLevel>
      <SecurePGPCCommunication>Disabled</SecurePGPCCommunication>
      <PutGetCommunication enabled="true"/>
      <WebserverProtection enabled="true" requireHttps="false"/>
    </Security>
    <Network>
      <Interface id="PROFINET_1" ip="{self.rand_ip()}" subnet="255.255.255.0"/>
    </Network>
  </Device>
</DeviceConfiguration>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Siemens S7 PLC — EDGE CASE — Sample {index} -->
<DeviceConfiguration version="2.9">
  <Device name="{hn}">
    <!-- Corrupted security node -->
    <Security/>
  </Device>
</DeviceConfiguration>
"""


# 2. Schneider Modicon PLC
class SchneiderPLCGenerator(ConfigGenerator):
    vendor = "Schneider Electric"
    product = "Modicon M580 / M241"
    os_name = "EcoStruxure"
    os_version = "v3.2"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/schneider_plc"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Schneider Modicon — SECURE — Sample {index} -->
<PLCConfiguration name="{hn}" target="M580">
  <CyberSecurityProfile>
    <Level>HighSecurity</Level>
    <UserAuthentication required="true" method="EncryptedToken" secret="{pwd}"/>
    <ModbusPortFiltering enabled="true">
      <AllowedIP>{self.rand_ip()}</AllowedIP>
    </ModbusPortFiltering>
    <EthernetIPSecurity secureEncap="true"/>
    <DisableUnusedProtocols ftp="true" http="true" snmpv1v2="true"/>
  </CyberSecurityProfile>
</PLCConfiguration>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Schneider Modicon — MISCONFIGURED — Sample {index} -->
<PLCConfiguration name="{hn}" target="M580">
  <CyberSecurityProfile>
    <Level>Disabled</Level>
    <UserAuthentication required="false"/>
    <ModbusPortFiltering enabled="false"/>
    <DisableUnusedProtocols ftp="false" http="false" snmpv1v2="false"/>
  </CyberSecurityProfile>
</PLCConfiguration>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Schneider Modicon — EDGE CASE — Sample {index} -->
<PLCConfiguration name="{hn}"/>
"""


# 3. Rockwell Allen-Bradley PLC
class RockwellPLCGenerator(ConfigGenerator):
    vendor = "Rockwell Automation"
    product = "ControlLogix 5580 / CompactLogix"
    os_name = "Studio 5000"
    os_version = "v34"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/rockwell_plc"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Rockwell ControlLogix — SECURE — Sample {index} -->
<RSLogix5000Project SchemaVersion="34.0">
  <Controller Name="{hn}">
    <CIPSecurity>
      <EtherNetIPSecurityMode>IntegrityAndConfidentiality</EtherNetIPSecurityMode>
      <TLSCipherSuites>TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384</TLSCipherSuites>
      <PreSharedKey value="{pwd}"/>
      <FactoryTalkSecurityPolicy enforceSecurity="true"/>
    </CIPSecurity>
  </Controller>
</RSLogix5000Project>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Rockwell ControlLogix — MISCONFIGURED — Sample {index} -->
<RSLogix5000Project SchemaVersion="34.0">
  <Controller Name="{hn}">
    <CIPSecurity>
      <EtherNetIPSecurityMode>NoSecurity</EtherNetIPSecurityMode>
      <FactoryTalkSecurityPolicy enforceSecurity="false"/>
    </CIPSecurity>
  </Controller>
</RSLogix5000Project>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Rockwell ControlLogix — EDGE CASE — Sample {index} -->
<RSLogix5000Project SchemaVersion="34.0">
  <Controller Name="{hn}"/>
</RSLogix5000Project>
"""


# 4. ABB Industrial PLC / RTU
class ABBIndustrialGenerator(ConfigGenerator):
    vendor = "ABB"
    product = "AC500 / RTU500"
    os_name = "Automation Builder"
    os_version = "v2.5"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/abb_industrial"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — ABB AC500 — SECURE — Sample {index} -->
<ABBConfiguration target="{hn}">
  <SecurityLevel>IEC62351_Compliant</SecurityLevel>
  <IEC60870_5_104 TLS="true" port="19999" auth="{pwd}"/>
  <WebAccess httpsOnly="true" sessionTimeout="300"/>
  <Firewall policy="drop-all">
    <Rule allowIP="{self.rand_ip()}" port="19999"/>
  </Firewall>
</ABBConfiguration>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — ABB AC500 — MISCONFIGURED — Sample {index} -->
<ABBConfiguration target="{hn}">
  <SecurityLevel>None</SecurityLevel>
  <IEC60870_5_104 TLS="false" port="2404"/>
  <WebAccess httpsOnly="false"/>
</ABBConfiguration>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — ABB AC500 — EDGE CASE — Sample {index} -->
<ABBConfiguration target="{hn}">
  <Firewall policy="drop-all"/>
</ABBConfiguration>
"""


# 5. Honeywell Building Automation
class HoneywellBuildingGenerator(ConfigGenerator):
    vendor = "Honeywell"
    product = "Niagara Framework N4 Controller"
    os_name = "Niagara 4"
    os_version = "4.12"
    device_type = "iot_building_automation"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/honeywell_building"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Honeywell Niagara — SECURE — Sample {index} -->
<station name="{hn}" version="4.12">
  <securityService>
    <passwordPolicy minLength="14" requireSpecialChar="true" maxFailedAttempts="3" lockoutMinutes="30"/>
    <tlsConfig requireTls="true" minTlsVersion="TLSv1.3"/>
    <foxService enabled="false"/>
    <foxsService enabled="true" port="4911" certAlias="honeywell-ca"/>
  </securityService>
</station>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Honeywell Niagara — MISCONFIGURED — Sample {index} -->
<station name="{hn}" version="4.12">
  <securityService>
    <passwordPolicy minLength="4" maxFailedAttempts="0"/>
    <foxService enabled="true" port="1911"/>
    <foxsService enabled="false"/>
  </securityService>
</station>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Honeywell Niagara — EDGE CASE — Sample {index} -->
<station name="{hn}">
  <securityService/>
</station>
"""


# 6. Beckhoff TwinCAT PLC
class BeckhoffTwinCATGenerator(ConfigGenerator):
    vendor = "Beckhoff"
    product = "CX5130 / CX9020 Embedded PC"
    os_name = "TwinCAT 3 / Windows 10 IoT"
    os_version = "TC3.1"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/beckhoff_twincat"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Beckhoff TwinCAT — SECURE — Sample {index} -->
<TcConfig>
  <TargetNetId>{self.rand_ip()}.1.1</TargetNetId>
  <Name>{hn}</Name>
  <AdsSecurity>
    <SecureAds enabled="true" requireAuth="true" certificateThumbprint="{pwd}"/>
    <IpWhitelist>
      <Address>{self.rand_ip()}</Address>
    </IpWhitelist>
  </AdsSecurity>
</TcConfig>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Beckhoff TwinCAT — MISCONFIGURED — Sample {index} -->
<TcConfig>
  <TargetNetId>{self.rand_ip()}.1.1</TargetNetId>
  <Name>{hn}</Name>
  <AdsSecurity>
    <SecureAds enabled="false" requireAuth="false"/>
  </AdsSecurity>
</TcConfig>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Beckhoff TwinCAT — EDGE CASE — Sample {index} -->
<TcConfig>
  <Name>{hn}</Name>
</TcConfig>
"""


# 7. WAGO PFC200 PLC
class WagoPLCGenerator(ConfigGenerator):
    vendor = "WAGO"
    product = "PFC200 Controller"
    os_name = "e!COCKPIT Linux"
    os_version = "FW23"
    device_type = "iot_plc"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "industrial/wago_plc"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "controller": hn,
            "security": {
                "ssh": {"enabled": True, "port": 22, "permit_root_login": False},
                "https_only": True,
                "tls_version": "1.3",
                "openvpn_enabled": True,
                "modbus_tcp_firewall": {"enabled": True, "allowed_ips": [self.rand_ip()]}
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "controller": hn,
            "security": {
                "telnet": {"enabled": True},
                "http_only": True,
                "ssh": {"permit_root_login": True},
                "modbus_tcp_firewall": {"enabled": False}
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"controller": hn, "security": {}}
        return json.dumps(cfg, indent=4)


# 8. Phoenix Contact PLCnext
class PhoenixContactGenerator(ConfigGenerator):
    vendor = "Phoenix Contact"
    product = "AXC F 2152 / 3152"
    os_name = "PLCnext Technology"
    os_version = "2023.0"
    device_type = "iot_plc"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "industrial/phoenix_contact"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "plc": hn,
            "user_management": {
                "security_profile": "High",
                "password_complexity": True,
                "session_timeout_seconds": 300
            },
            "firewall": {
                "input_policy": "DROP",
                "allow_services": ["ssh", "https"]
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "plc": hn,
            "user_management": {"security_profile": "None"},
            "firewall": {"input_policy": "ACCEPT"}
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"plc": hn}
        return json.dumps(cfg, indent=4)


# 9. Mitsubishi MELSEC PLC
class MitsubishiPLCGenerator(ConfigGenerator):
    vendor = "Mitsubishi Electric"
    product = "MELSEC iQ-R / iQ-F"
    os_name = "GX Works3"
    os_version = "v1.08"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/mitsubishi_plc"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Mitsubishi MELSEC — SECURE — Sample {index} -->
<MelsecConfig cpu="{hn}">
  <IpFilter enabled="true">
    <AllowRange start="{self.rand_ip()}" end="{self.rand_ip()}"/>
  </IpFilter>
  <SlmpSecurity authenticationRequired="true" encryptionKey="{pwd}"/>
</MelsecConfig>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Mitsubishi MELSEC — MISCONFIGURED — Sample {index} -->
<MelsecConfig cpu="{hn}">
  <IpFilter enabled="false"/>
  <SlmpSecurity authenticationRequired="false"/>
</MelsecConfig>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Mitsubishi MELSEC — EDGE CASE — Sample {index} -->
<MelsecConfig cpu="{hn}"/>
"""


# 10. Omron Sysmac PLC
class OmronPLCGenerator(ConfigGenerator):
    vendor = "Omron"
    product = "Sysmac NJ/NX Series"
    os_name = "Sysmac Studio"
    os_version = "v1.50"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/omron_plc"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Omron Sysmac — SECURE — Sample {index} -->
<SysmacSecurity unit="{hn}">
  <OperationRights enabled="true" adminPassword="{pwd}"/>
  <PacketFilter enabled="true">
    <Rule protocol="EtherNetIP" action="permit" ip="{self.rand_ip()}"/>
    <Rule protocol="All" action="deny"/>
  </PacketFilter>
</SysmacSecurity>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Omron Sysmac — MISCONFIGURED — Sample {index} -->
<SysmacSecurity unit="{hn}">
  <OperationRights enabled="false"/>
  <PacketFilter enabled="false"/>
</SysmacSecurity>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Omron Sysmac — EDGE CASE — Sample {index} -->
<SysmacSecurity unit="{hn}"/>
"""


# 11. Emerson DeltaV DCS
class EmersonDeltaVGenerator(ConfigGenerator):
    vendor = "Emerson"
    product = "DeltaV DCS / Ovation"
    os_name = "DeltaV Security Suite"
    os_version = "v14.x"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/emerson_deltav"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Emerson DeltaV — SECURE — Sample {index} -->
<DeltaVSecurity node="{hn}">
  <NodeLockdown enabled="true"/>
  <SmartFirewall incomingBlocked="true" auditTrail="true"/>
  <WhitelistedControllers>
    <Controller ip="{self.rand_ip()}" key="{pwd}"/>
  </WhitelistedControllers>
</DeltaVSecurity>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Emerson DeltaV — MISCONFIGURED — Sample {index} -->
<DeltaVSecurity node="{hn}">
  <NodeLockdown enabled="false"/>
  <SmartFirewall incomingBlocked="false"/>
</DeltaVSecurity>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Emerson DeltaV — EDGE CASE — Sample {index} -->
<DeltaVSecurity node="{hn}"/>
"""


# 12. GE Vernova Mark VIe
class GEVernovaGenerator(ConfigGenerator):
    vendor = "GE Vernova"
    product = "Mark VIe / PACSystems RX3i"
    os_name = "Machine Edition"
    os_version = "v9.8"
    device_type = "iot_plc"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "industrial/ge_vernova"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — GE Vernova — SECURE — Sample {index} -->
<MarkVIePolicy system="{hn}">
  <DNP3SecureAuth version="SAv5" key="{pwd}"/>
  <LogicProtection writeLock="true"/>
  <UDBCertificateCheck strict="true"/>
</MarkVIePolicy>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — GE Vernova — MISCONFIGURED — Sample {index} -->
<MarkVIePolicy system="{hn}">
  <DNP3SecureAuth version="disabled"/>
  <LogicProtection writeLock="false"/>
</MarkVIePolicy>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — GE Vernova — EDGE CASE — Sample {index} -->
<MarkVIePolicy system="{hn}"/>
"""


# =============================================================================
# IP CAMERAS (4)
# =============================================================================

# 13. Axis IP Camera
class AxisIPCamGenerator(ConfigGenerator):
    vendor = "Axis Communications"
    product = "Axis Q35 / P32 Series"
    os_name = "AXIS OS"
    os_version = "11.x"
    device_type = "iot_camera"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "cameras/axis_ipcam"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "root": {
                "Properties": {"System": {"SerialNumber": hn}},
                "Network": {
                    "HTTP": {"Enabled": "no"},
                    "HTTPS": {"Enabled": "yes", "StrictTransportSecurity": "yes", "Ciphers": "HIGH"},
                    "IEEE8021X": {"Enabled": "yes", "EAPOLVersion": "3"},
                    "RTSP": {"OverHTTP": "no", "OverHTTPS": "yes"},
                    "SSH": {"Enabled": "no"}
                },
                "System": {
                    "Accounts": {"root": {"Password": pwd, "RemoteLogin": "no"}}
                }
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "root": {
                "Properties": {"System": {"SerialNumber": hn}},
                "Network": {
                    "HTTP": {"Enabled": "yes", "Port": "80"},
                    "HTTPS": {"Enabled": "no"},
                    "SSH": {"Enabled": "yes"},
                    "UPnP": {"Enabled": "yes"}
                },
                "System": {
                    "Accounts": {"root": {"Password": "root"}}
                }
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"root": {"Network": {}}}
        return json.dumps(cfg, indent=4)


# 14. Hikvision IP Camera
class HikvisionIPCamGenerator(ConfigGenerator):
    vendor = "Hikvision"
    product = "DS-2CD Series"
    os_name = "Hikvision Firmware"
    os_version = "V5.7"
    device_type = "iot_camera"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "cameras/hikvision_ipcam"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Hikvision Camera — SECURE — Sample {index} -->
<SecurityConfig version="2.0">
  <DeviceName>{hn}</DeviceName>
  <IllegalLoginLock enabled="true" maxAttempts="3" lockTimeMinutes="30"/>
  <HTTPSPort enabled="true" port="443"/>
  <HTTPPort enabled="false"/>
  <ONVIFSecurity authType="digest" digestAlgorithm="SHA256"/>
  <SecurityAuditLog enabled="true"/>
  <AdminPassword encrypted="true">{pwd}</AdminPassword>
</SecurityConfig>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Hikvision Camera — MISCONFIGURED — Sample {index} -->
<SecurityConfig version="2.0">
  <DeviceName>{hn}</DeviceName>
  <IllegalLoginLock enabled="false"/>
  <HTTPPort enabled="true" port="80"/>
  <HTTPSPort enabled="false"/>
  <ONVIFSecurity authType="none"/>
  <AdminPassword encrypted="false">12345</AdminPassword>
</SecurityConfig>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Hikvision Camera — EDGE CASE — Sample {index} -->
<SecurityConfig version="2.0">
  <DeviceName>{hn}</DeviceName>
</SecurityConfig>
"""


# 15. Dahua IP Camera
class DahuaIPCamGenerator(ConfigGenerator):
    vendor = "Dahua Technology"
    product = "IPC-HFW / IPC-HDW"
    os_name = "Dahua Firmware"
    os_version = "V4.0"
    device_type = "iot_camera"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "cameras/dahua_ipcam"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "device": hn,
            "Security": {
                "IPFilter": {"Enable": True, "Mode": "WhiteList", "IPList": [self.rand_ip()]},
                "HTTPS": {"Enable": True, "CertificateInstalled": True},
                "P2P": {"Enable": False},
                "ONVIFAuth": "Digest",
                "Password": pwd
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "device": hn,
            "Security": {
                "IPFilter": {"Enable": False},
                "HTTPS": {"Enable": False},
                "P2P": {"Enable": True},
                "Password": "admin"
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"device": hn, "Security": {}}
        return json.dumps(cfg, indent=4)


# 16. Hanwha Wisenet IP Camera
class HanwhaIPCamGenerator(ConfigGenerator):
    vendor = "Hanwha Vision"
    product = "Wisenet X-Series"
    os_name = "Wisenet OS"
    os_version = "v2.x"
    device_type = "iot_camera"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "cameras/hanwha_ipcam"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "camera": hn,
            "security": {
                "tpm_2_0_active": True,
                "secure_boot": True,
                "https_mandatory": True,
                "digest_auth_rtsp": True,
                "admin_pass": pwd
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "camera": hn,
            "security": {
                "tpm_2_0_active": False,
                "https_mandatory": False,
                "admin_pass": "4321"
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"camera": hn}
        return json.dumps(cfg, indent=4)


# =============================================================================
# IOT GATEWAYS (4)
# =============================================================================

# 17. Teltonika RutOS Gateway
class TeltonikaRutOSGenerator(ConfigGenerator):
    vendor = "Teltonika Networks"
    product = "RUTX09 / RUT240 Cellular Router"
    os_name = "RutOS"
    os_version = "7.x"
    device_type = "iot_gateway"
    category = "iot"
    config_format = "ini"
    vendor_dir_name = "gateways/teltonika_rutos"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        syslog = self.rand_syslog()
        return f"""# GAACA Dataset — Teltonika RutOS — SECURE — Sample {index}
package system
config system
    option hostname '{hn}'
    option timezone 'UTC'

package dropbear
config dropbear
    option Port '22'
    option PasswordAuth 'off'
    option RootPasswordAuth 'off'

package uhttpd
config uhttpd main
    list listen_https '0.0.0.0:443'
    option redirect_https '1'

package firewall
config defaults
    option syn_flood '1'
    option input 'DROP'
    option output 'ACCEPT'
    option forward 'DROP'
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Teltonika RutOS — MISCONFIGURED — Sample {index}
package dropbear
config dropbear
    option Port '22'
    option PasswordAuth 'on'
    option RootPasswordAuth 'on'

package uhttpd
config uhttpd main
    list listen_http '0.0.0.0:80'
    option redirect_https '0'

package firewall
config defaults
    option input 'ACCEPT'
    option forward 'ACCEPT'
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Teltonika RutOS — EDGE CASE — Sample {index}
package firewall
! corrupted UCI block
"""


# 18. Moxa Industrial Gateway
class MoxaIndustrialGenerator(ConfigGenerator):
    vendor = "Moxa"
    product = "OnCell G3150A / EDS-G512E"
    os_name = "Moxa OS"
    os_version = "v3"
    device_type = "iot_gateway"
    category = "iot"
    config_format = "ini"
    vendor_dir_name = "gateways/moxa_industrial"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""# GAACA Dataset — Moxa Industrial — SECURE — Sample {index}
SysName={hn}
TelnetEnable=0
SSHEnable=1
HTTPEnable=0
HTTPSEnable=1
AdminPassword={pwd}
IPFilterEnable=1
IPFilterAllowIP={self.rand_ip()}
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Moxa Industrial — MISCONFIGURED — Sample {index}
SysName={hn}
TelnetEnable=1
SSHEnable=0
HTTPEnable=1
HTTPSEnable=0
AdminPassword=moxa
IPFilterEnable=0
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Moxa Industrial — EDGE CASE — Sample {index}
SysName={hn}
"""


# 19. Advantech WISE IoT Gateway
class AdvantechWiseGenerator(ConfigGenerator):
    vendor = "Advantech"
    product = "WISE-710 / ADAM-6700"
    os_name = "WISE-EdgeLink"
    os_version = "v2"
    device_type = "iot_gateway"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "gateways/advantech_wise"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "device": hn,
            "mqtt": {
                "broker": "tls://198.51.100.200:8883",
                "tls_cert_validation": True,
                "client_id": hn,
                "auth": {"user": "iot-agent", "pass": pwd}
            },
            "security": {"firewall": "strict", "ssh_key_only": True}
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "device": hn,
            "mqtt": {
                "broker": "tcp://198.51.100.200:1883",
                "auth": {"anonymous": True}
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"device": hn, "mqtt": {}}
        return json.dumps(cfg, indent=4)


# 20. Quectel Cellular Gateway
class QuectelCellularGenerator(ConfigGenerator):
    vendor = "Quectel"
    product = "BG95 / EC25 IoT Gateway"
    os_name = "ThreadX / Linux"
    os_version = "v1"
    device_type = "iot_gateway"
    category = "iot"
    config_format = "ini"
    vendor_dir_name = "gateways/quectel_cellular"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""# GAACA Dataset — Quectel Cellular — SECURE — Sample {index}
AT+CGDCONT=1,"IP","private.apn"
AT+QSSLCFG="sslversion",1,4
AT+QSSLCFG="ciphersuite",1,0XFFFF
AT+QFLOCK="PIN","{pwd}"
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Quectel Cellular — MISCONFIGURED — Sample {index}
AT+CGDCONT=1,"IP","internet"
AT+QSSLCFG="sslversion",1,0
AT+QFLOCK="NONE"
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""# GAACA Dataset — Quectel Cellular — EDGE CASE — Sample {index}
AT+CGDCONT=1
"""


# =============================================================================
# SMART DEVICES (5)
# =============================================================================

# 21. Tasmota ESP8266/ESP32
class TasmotaGenerator(ConfigGenerator):
    vendor = "Tasmota Open Source"
    product = "Sonoff / Shelly with Tasmota"
    os_name = "Tasmota Firmware"
    os_version = "13.x"
    device_type = "iot_sensor"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "smart_devices/tasmota"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "NAME": hn,
            "WebPassword": pwd,
            "MqttHost": "198.51.100.220",
            "MqttPort": 8883,
            "MqttUser": "tasmota_sec",
            "MqttPassword": pwd,
            "SetOption13": 1,
            "SetOption103": 1
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "NAME": hn,
            "WebPassword": "",
            "MqttHost": "198.51.100.220",
            "MqttPort": 1883,
            "MqttUser": "",
            "MqttPassword": ""
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"NAME": hn}
        return json.dumps(cfg, indent=4)


# 22. Espressif ESP-IDF / ESPHome
class EspressifESPGenerator(ConfigGenerator):
    vendor = "Espressif Systems"
    product = "ESP32-S3 / ESPHome"
    os_name = "ESP-IDF"
    os_version = "v5.1"
    device_type = "iot_sensor"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "smart_devices/espressif_esp"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "esphome": {"name": hn},
            "wifi": {
                "ssid": "Secure-IoT",
                "password": pwd,
                "eap": {"identity": "esp32", "ca_cert": "CERT_DATA"}
            },
            "ota": {"password": pwd},
            "api": {"encryption": {"key": pwd}}
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "esphome": {"name": hn},
            "wifi": {"ssid": "Open-IoT", "password": ""},
            "ota": {"password": ""},
            "api": {}
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"esphome": {"name": hn}}
        return json.dumps(cfg, indent=4)


# 23. Particle IoT
class ParticleIoTGenerator(ConfigGenerator):
    vendor = "Particle"
    product = "Boron / Photon 2"
    os_name = "Device OS"
    os_version = "v5.x"
    device_type = "iot_sensor"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "smart_devices/particle_iot"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "deviceId": hn,
            "security": {
                "serverPublicKey": pwd,
                "sessionTicketTLS": True,
                "lockProtected": True
            }
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "deviceId": hn,
            "security": {"lockProtected": False}
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"deviceId": hn}
        return json.dumps(cfg, indent=4)


# 24. Johnson Controls Metasys
class JohnsonControlsGenerator(ConfigGenerator):
    vendor = "Johnson Controls"
    product = "Metasys NAE / SNE"
    os_name = "Metasys OS"
    os_version = "v12"
    device_type = "iot_building_automation"
    category = "iot"
    config_format = "xml"
    vendor_dir_name = "smart_devices/johnson_controls"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Johnson Controls Metasys — SECURE — Sample {index} -->
<MetasysSecurity engine="{hn}">
  <BACnetSC enabled="true" primaryHub="{self.rand_ip()}" hubCertificateThumbprint="{pwd}"/>
  <AuthenticationMode>EncryptedTokenOnly</AuthenticationMode>
  <AuditLog enabled="true"/>
</MetasysSecurity>
"""

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Johnson Controls Metasys — MISCONFIGURED — Sample {index} -->
<MetasysSecurity engine="{hn}">
  <BACnetIP unencrypted="true" port="47808"/>
  <AuthenticationMode>None</AuthenticationMode>
</MetasysSecurity>
"""

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GAACA Dataset — Johnson Controls Metasys — EDGE CASE — Sample {index} -->
<MetasysSecurity engine="{hn}"/>
"""


# 25. Shelly Smart IoT
class ShellyIoTGenerator(ConfigGenerator):
    vendor = "Shelly"
    product = "Shelly Plus 1 / Pro 4PM"
    os_name = "Mongoose OS"
    os_version = "v1.0"
    device_type = "iot_sensor"
    category = "iot"
    config_format = "json"
    vendor_dir_name = "smart_devices/shelly_iot"

    def generate_secure(self, index: int) -> str:
        hn = self.rand_hostname()
        pwd = self.rand_password()
        cfg = {
            "id": hn,
            "auth": {"enable": True, "user": "admin", "pass": pwd},
            "mqtt": {"enable": True, "ssl_ca": "ca.pem", "server": "198.51.100.210:8883"},
            "cloud": {"enable": False}
        }
        return json.dumps(cfg, indent=4)

    def generate_misconfigured(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {
            "id": hn,
            "auth": {"enable": False},
            "mqtt": {"enable": True, "server": "198.51.100.210:1883"}
        }
        return json.dumps(cfg, indent=4)

    def generate_edge_case(self, index: int) -> str:
        hn = self.rand_hostname()
        cfg = {"id": hn}
        return json.dumps(cfg, indent=4)


# =============================================================================
# Registry of all IoT generators
# =============================================================================
IOT_GENERATORS = [
    SiemensPLCGenerator,
    SchneiderPLCGenerator,
    RockwellPLCGenerator,
    ABBIndustrialGenerator,
    HoneywellBuildingGenerator,
    BeckhoffTwinCATGenerator,
    WagoPLCGenerator,
    PhoenixContactGenerator,
    MitsubishiPLCGenerator,
    OmronPLCGenerator,
    EmersonDeltaVGenerator,
    GEVernovaGenerator,
    AxisIPCamGenerator,
    HikvisionIPCamGenerator,
    DahuaIPCamGenerator,
    HanwhaIPCamGenerator,
    TeltonikaRutOSGenerator,
    MoxaIndustrialGenerator,
    AdvantechWiseGenerator,
    QuectelCellularGenerator,
    TasmotaGenerator,
    EspressifESPGenerator,
    ParticleIoTGenerator,
    JohnsonControlsGenerator,
    ShellyIoTGenerator,
]
